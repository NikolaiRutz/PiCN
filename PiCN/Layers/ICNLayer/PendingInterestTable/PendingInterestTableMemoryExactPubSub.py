import time

from typing import List
from PiCN.Layers.ICNLayer.PendingInterestTable.PendingInterestTableMemoryExact import PendingInterstTableMemoryExact, \
    PendingInterestTableEntry
from PiCN.Layers.ICNLayer.PendingInterestTable.BasePendingInterestTable import BasePendingInterestTable, \
    PendingInterestTableEntry
from PiCN.Layers.ICNLayer.ForwardingInformationBase import ForwardingInformationBaseEntry
from PiCN.Packets import Interest, Name
import re

"""PIT for Pub/Sub Model"""


class PendingInterestTableMemoryExactPubSub(PendingInterstTableMemoryExact):

    def __init__(self, pit_timeout: int = 10, pit_retransmits: int = 3, pub_sub: int = -1):
        BasePendingInterestTable.__init__(self, pit_timeout=pit_timeout, pit_retransmits=pit_retransmits)
        self.pub_sub = pub_sub

    # TODO: clean this code
    # regex expression noch nicht ganz richtig (auch true wenn kein Wert in den Klammern steht)
    def is_pub_sub(self, name: Name) -> bool:
        sub_name = name.components[-1].decode("utf-8")
        return bool(re.search("subscribe\(\d*\)", sub_name))

    #TODO: gleicher subscribe interest soll beim adden überprüft werden, ob findPIT dazu existiert; falls ja soll die FaceID ersetzt werden?
    def add_pit_entry(self, name, faceid: int, interest: Interest = None, local_app=False):
        sub_value = self.extract_sub_value(name)
        if sub_value >= 0:
            name = Name(name.components[:-1])
        for pit_entry in self.container:
            if pit_entry.name == name:
                if faceid in pit_entry.face_id and local_app in pit_entry.local_app:
                    return
                self.container.remove(pit_entry)
                pit_entry._faceids.append(faceid)
                pit_entry._local_app.append(local_app)
                if sub_value >= 0:
                    pit_entry.pub_sub = sub_value
                self.container.append(pit_entry)
                return

        pub_sub_value = -1
        if sub_value >= 0:
            pub_sub_value = sub_value
        self.container.append(
            PendingInterestTableEntry(name, faceid, interest, local_app, pub_sub=pub_sub_value))

    def extract_sub_value(self, name: Name) -> int:
        return int(re.findall('\d+', name.components[-1].decode("utf-8"))[0])

    def remove_pit_entry(self, name: Name):
        to_remove = []
        for pit_entry in self.container:
            if (pit_entry.name == name):
                if pit_entry.pub_sub >= 0:
                    continue
                to_remove.append(pit_entry)
        for r in to_remove:
            self.container.remove(r)

    # TODO: wenn findtPIT wird ein findPit value erstellt. Durchsuche PIT mit subscribe nach vorhandenen gleichen findPIT einträgen
    def find_pit_entry(self, name: Name) -> PendingInterestTableEntry:
        for pit_entry in self.container:
            if (pit_entry.name == name):
                return pit_entry
            if (self.is_pub_sub(name)):
                #TODO: wenn pubSub muss überprüft werden, ob findPIT dazu existiert (data/findPit(5)-> FaceID zurückgeben, wenn data/sub(10) kommt zb
                sub_entry_name = Name(pit_entry.name.components[:-1])
                if (sub_entry_name == pit_entry.name):
                    return pit_entry
            if pit_entry.pub_sub >= 0:
                sub_entry_name = Name(name.components[:])
                if len(sub_entry_name) < len(pit_entry.name):
                    return None
                for i in range(min(pit_entry.pub_sub + 1, len(name.components))):
                    if (sub_entry_name == pit_entry.name):
                        return pit_entry
                    sub_entry_name.components.pop()
        return None

    def find_face_ids(self, name: Name) -> list:
        face_ids = []
        for pit_entry in self.container:
            if (pit_entry.name == name):
                for pit_entry_faceid in pit_entry.faceids:
                    if pit_entry_faceid not in face_ids:
                        face_ids.append(pit_entry_faceid)
            if pit_entry.pub_sub >= 0:
                sub_entry_name = Name(name.components[:])
                if len(sub_entry_name) < len(pit_entry.name):
                    continue
                for i in range(min(pit_entry.pub_sub + 1, len(name.components))):

                    if (sub_entry_name == pit_entry.name):

                        for pit_entry_faceid in pit_entry.faceids:
                            if pit_entry_faceid not in face_ids:
                                face_ids.append(pit_entry_faceid)
                    sub_entry_name.components.pop()
        return face_ids

    def ageing(self) -> List[PendingInterestTableEntry]:
        cur_time = time.time()
        remove = []
        updated = []
        for pit_entry in self.container:
            if pit_entry.pub_sub >= 0:
                continue
            if pit_entry.timestamp + self._pit_timeout < cur_time and pit_entry.retransmits > self._pit_retransmits:
                remove.append(pit_entry)
            else:
                pit_entry.retransmits = pit_entry.retransmits + 1
                updated.append(pit_entry)
        for pit_entry in remove:
            if pit_entry.pub_sub >= 0:
                continue
            self.remove_pit_entry(pit_entry.name)
        for pit_entry in updated:
            if pit_entry.pub_sub >= 0:
                continue
            self.remove_pit_entry(pit_entry.name)
            self.container.append(pit_entry)
        return updated, remove
