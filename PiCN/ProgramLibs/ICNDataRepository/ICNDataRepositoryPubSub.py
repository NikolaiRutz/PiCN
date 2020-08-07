from typing import Optional

import multiprocessing
from typing import List

from PiCN.LayerStack.LayerStack import LayerStack
from PiCN.Layers.ChunkLayer import BasicChunkLayer
from PiCN.Layers.PacketEncodingLayer import BasicPacketEncodingLayer
from PiCN.Layers.RepositoryLayer import BasicRepositoryLayer
from PiCN.Layers.AutoconfigLayer import AutoconfigRepoLayer

from PiCN.Layers.ChunkLayer.Chunkifyer import SimpleContentChunkifyer
from PiCN.Layers.LinkLayer import BasicLinkLayer
from PiCN.Layers.LinkLayer.FaceIDTable import FaceIDDict
from PiCN.Layers.LinkLayer.Interfaces import UDP4Interface, BaseInterface
from PiCN.Processes.PiCNSyncDataStructFactory import PiCNSyncDataStructFactory
from PiCN.Layers.PacketEncodingLayer.Encoder import SimpleStringEncoder
from PiCN.Layers.PacketEncodingLayer.Encoder import BasicEncoder
from PiCN.Layers.RepositoryLayer.Repository import BaseRepository, SimpleFileSystemRepository, SimpleMemoryRepository
from PiCN.Layers.ThunkLayer.PlanTable import PlanTable
from PiCN.Layers.ThunkLayer.ThunkTable import ThunkList
from PiCN.Layers.ThunkLayer.BasicThunkLayer import BasicThunkLayer
from PiCN.Layers.NFNLayer.Parser import DefaultNFNParser
from PiCN.Logger import Logger
from PiCN.Packets import Name
from PiCN.Mgmt import Mgmt
from PiCN.ProgramLibs.ICNDataRepository import ICNDataRepository
from PiCN.Layers.RepositoryLayer import PubSubRepositoryLayer


class ICNDataRepositoryPubSub(ICNDataRepository):

    def __init__(self, foldername: Optional[str], prefix: Name,
                 port=9000, log_level=255, encoder: BasicEncoder = None,
                 autoconfig: bool = False, autoconfig_routed: bool = False, interfaces: List[BaseInterface] = None,
                 use_thunks=False):
        ICNDataRepository.__init__(self, foldername=foldername, prefix=prefix, port=port, log_level=log_level, encoder=encoder,
              autoconfig=autoconfig, autoconfig_routed=autoconfig_routed, interfaces=interfaces,
              use_thunks=use_thunks, repolayer=PubSubRepositoryLayer(log_level=log_level))
        self.repolayer._repository = self.repo

