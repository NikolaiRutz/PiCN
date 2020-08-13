import multiprocessing

from PiCN.Layers.RepositoryLayer.Repository import BaseRepository
from PiCN.Layers.RepositoryLayer import BasicRepositoryLayer
from PiCN.Packets import Interest, Content, Packet, Nack, NackReason
from PiCN.Processes import LayerProcess
from PiCN.Packets import Content, Interest, Name
import re
from collections import defaultdict



class PubSubRepositoryLayer(BasicRepositoryLayer):

    def __init__(self, repository: BaseRepository = None, propagate_interest: bool = False, logger_name="RepoLayer",
                 log_level=255):
        BasicRepositoryLayer.__init__(self, repository=repository, propagate_interest=propagate_interest,
                                      logger_name=logger_name,
                                      log_level=log_level)
        self._subscribtion_list = defaultdict(list)


    # TODO: add content funktion (Liste mit subscirbern durchgehen und senden und ins repo legen) soll SimpleRepo aufrufen
    def add_content(self, name: Name, data):
        self._repository.add_content(name, data)
        self.check_subscription(name,data)
        return

    #TODO: synch. needed
    def check_subscription(self, name: Name, data):
        for sub_element in self._subscribtion_list:
            for sub_index in range (sub_element[1]):
                if name.components[-1 - sub_index] == sub_element[0]:
                    self.propagate_content(self._subscribtion_list[sub_element], data)

    def propagate_content(self, face_id: list, data):
        for i in face_id:
            self.queue_to_lower.put([i, data])

    #TODO: clean this code. This two methods are also in PITMemoryExactPS
    def is_pub_sub(self, name: Name) -> bool:
        sub_name = name.components[-1].decode("utf-8")
        return bool(re.search("subscribe\(\d*\)", sub_name))

    def extract_sub_value(self, name: Name) -> int:
        return int(re.findall('\d+', name.components[-1].decode("utf-8"))[0])

    # TODO: PS einfügen(content objekt mit approved bei ersten nachricht) / Map erstellen mit allen FaceIDs zu dem entsprechendem subscribe
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
            # wenn subscribe schon existiert dann wird interface geadded, sonst wird ein neuer Eintrag erstellt mit Face
            elif self.is_pub_sub(packet.name):
                # list index kann out of range sein. Kann gehandelt werden aber vorest aufpassen
                sub_length = self.extract_sub_value(packet.name)

                path_name = packet.name.components[-1 - sub_length]
                if faceid not in self._subscribtion_list[(path_name, sub_length)]:
                    self._subscribtion_list[(path_name, sub_length)].append(faceid)
                    #TODO: content richtig erstellen/ack für sub
                    content = self._repository.get_content(packet.name)
                    self.queue_to_lower.put([0, content])
                else:
                    #TODO: add handler for already subscribed faces
                    print("already subscribed")

            else:
                self.logger.info("No matching data, dropping interest, sending nack")
                nack = Nack(packet.name, NackReason.NO_CONTENT, interest=packet)
                to_lower.put([faceid, nack])
                return
        if isinstance(packet, Content):
            pass
