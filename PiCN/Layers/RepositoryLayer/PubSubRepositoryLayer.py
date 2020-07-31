import multiprocessing

from PiCN.Layers.RepositoryLayer.Repository import BaseRepository
from PiCN.Layers.RepositoryLayer import BasicRepositoryLayer
from PiCN.Packets import Interest, Content, Packet, Nack, NackReason
from PiCN.Processes import LayerProcess
from PiCN.Packets import Content, Interest, Name


class PubSubRepositoryLayer(BasicRepositoryLayer):

    def __init__(self, repository: BaseRepository, propagate_interest: bool = False, logger_name="RepoLayer",
                 log_level=255):
        BasicRepositoryLayer.__init__(self, repository=repository, propagate_interest=propagate_interest,
                                      logger_name=logger_name,
                                      log_level=log_level)

    # TODO: add content funktion (Liste mit subscirbern durchgehen und senden und ins repo legen)
    def add_content(self, name: Name, data):
        return

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
                # packete zurücksenden
                self.queue_to_lower.put([faceid, packet])
                return
            else:
                self.logger.info("No matching data, dropping interest, sending nack")
                nack = Nack(packet.name, NackReason.NO_CONTENT, interest=packet)
                to_lower.put([faceid, nack])
                return
        if isinstance(packet, Content):
            pass
