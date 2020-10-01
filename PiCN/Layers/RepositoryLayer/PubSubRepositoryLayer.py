import multiprocessing

from PiCN.Layers.RepositoryLayer.Repository import BaseRepository
from PiCN.Layers.RepositoryLayer import BasicRepositoryLayer
from PiCN.Packets import Interest, Content, Packet, Nack, NackReason
from PiCN.Processes import LayerProcess
from PiCN.Packets import Content, Interest, Name
import re
from collections import defaultdict


class PubSubRepositoryLayer(BasicRepositoryLayer):

    #TODO: add Interest broadcast wenn sich repo bewegt
    def __init__(self, repository: BaseRepository = None, propagate_interest: bool = False, logger_name="RepoLayer",
                 log_level=255):
        BasicRepositoryLayer.__init__(self, repository=repository, propagate_interest=propagate_interest,
                                      logger_name=logger_name,
                                      log_level=log_level)

    def add_content(self, name: Name, data: Content):
        self._repository.add_content(name, data)
        self.check_subscription(name, data)
        return

    def check_subscription(self, name: Name, data):
        face_id = []
        for sub_element in self._repository._subscribtion_list:
            sub_entry_name = Name(name.components[:])
            if len(name) < len(sub_element[0]):
                continue
            for sub_index in range(min(sub_element[1] + 1, len(name))):
                if sub_entry_name == sub_element[0]:
                    for elem in self._repository._subscribtion_list[sub_element]:
                        if elem not in face_id:
                            face_id.append(elem)
                sub_entry_name.components.pop()
        self.propagate_content(face_id, Content(name, data))

    def propagate_content(self, face_id: list, data):
        inter = Interest(Name("/data0/findPit(5)"))
        for i in face_id:
            self.queue_to_lower.put([i, inter])
            self.queue_to_lower.put([i, data])
            self.logger.info("Updating Subscriber about added content. FaceID: " + str(i))

    # TODO: clean this code. This two methods are also in PITMemoryExactPS
    def is_pub_sub(self, name: Name) -> bool:
        sub_name = name.components[-1].decode("utf-8")
        return bool(re.search("subscribe\(\d*\)", sub_name))

    def extract_sub_value(self, name: Name) -> int:
        return int(re.findall('\d+', name.components[-1].decode("utf-8"))[0])

    def data_from_lower(self, to_lower: multiprocessing.Queue, to_higher: multiprocessing.Queue, data: Packet):
        self.logger.info("Got Data from lower")
        if self._repository is None:
            return
        faceid = data[0]
        packet = data[1]

        if isinstance(packet, Interest):
            if self._repository.is_content_available(packet.name):
                c = self._repository.get_content(packet.name)
                self.queue_to_lower.put([faceid, c])
                self.logger.info("Found content object, sending down")
                return
            elif self._proagate_interest is True:
                self.queue_to_lower.put([faceid, packet])
                return
            # TODO: subsciption list fix (hinter Teil muss auch matchen; kann nur im Subnamen gleich sein)
            # wenn subscribe schon existiert dann wird interface geadded, sonst wird ein neuer Eintrag erstellt mit Face
            elif self.is_pub_sub(packet.name):
                # list index kann out of range sein. Kann gehandelt werden aber vorest aufpassen
                sub_length = self.extract_sub_value(packet.name)
                path_name = Name(packet.name.components[:-1])

                if (path_name, sub_length) not in self._repository._subscribtion_list:
                    self._repository._subscribtion_list[(path_name, sub_length)] = [faceid]
                elif faceid not in self._repository._subscribtion_list[(path_name, sub_length)]:
                    faceid_to_update = list(self._repository._subscribtion_list[(path_name, sub_length)])
                    faceid_to_update.append(faceid)
                    self._repository._subscribtion_list[(path_name, sub_length)] = faceid_to_update
                    # TODO: content richtig erstellen/ack für sub
                    content = self._repository.get_content(packet.name)
                    if content == None:
                        return
                    self.queue_to_lower.put([0, content])
                else:
                    self.logger.info("already subscribed. Face ID: " + str(faceid))
            else:
                self.logger.info("No matching data, dropping interest, sending nack")
                nack = Nack(packet.name, NackReason.NO_CONTENT, interest=packet)
                to_lower.put([faceid, nack])
                return
        if isinstance(packet, Content):
            pass
