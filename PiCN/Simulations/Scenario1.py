from PiCN.Processes import PiCNSyncDataStructFactory
from PiCN.ProgramLibs.Fetch import Fetch
from PiCN.ProgramLibs.ICNForwarder import ICNForwarder
from PiCN.Layers.LinkLayer.Interfaces import SimulationBus
from PiCN.Layers.LinkLayer.Interfaces import AddressInfo
from PiCN.Layers.PacketEncodingLayer.Encoder import BasicEncoder, SimpleStringEncoder, NdnTlvEncoder
from PiCN.Mgmt import MgmtClient
from PiCN.Packets import Content, Interest, Name
from PiCN.Layers.ICNLayer.PendingInterestTable.PendingInterestTableMemoryExactPubSub import \
    PendingInterestTableMemoryExactPubSub
from PiCN.ProgramLibs.ICNDataRepository import ICNDataRepository, ICNDataRepositoryPubSub
import time

if __name__ == "__main__":
    simulation_bus = SimulationBus(packetencoder=NdnTlvEncoder())

    # Pub-Sub Pit
    synced_data_struct_factory = PiCNSyncDataStructFactory()
    synced_data_struct_factory.register("pit", PendingInterestTableMemoryExactPubSub)
    synced_data_struct_factory.create_manager()

    # ICN Forwarder 0
    icn_fwd0 = ICNForwarder(port=0, encoder=NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("icn0")],
                            log_level=255, ageing_interval=1)

    # PS PIT
    icn_fwd0.icnlayer.pit = synced_data_struct_factory.manager.pit(pub_sub=True)


    # PS Repos
    icn_repo0 = ICNDataRepositoryPubSub(foldername=None, prefix=Name("/data0"), port=0,
                                        interfaces=[simulation_bus.add_interface("repo0")], encoder=NdnTlvEncoder(),
                                        log_level=255)


    # Fetchtools
    fetch_tool_0 = Fetch("icn0", None, 255, NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("fetchtool0")],
                         face_id=0)

    mgmt_client0 = MgmtClient(icn_fwd0.mgmt.mgmt_sock.getsockname()[1])

    # start everything
    icn_fwd0.start_forwarder()
    icn_repo0.start_repo()
    simulation_bus.start_process()

    # interfaces the content is forwarded to
    mgmt_client0.add_face("repo0", None, 0)

    mgmt_client0.add_forwarding_rule(Name("/data0"), [0])

    # Test1: fetchtool0 content subscription
    name0 = Name("/data0/subscribe(10)")
    fetch_tool_0.listen_for_content(name0)

    time.sleep(3)

    icn_repo0.repolayer.add_content(Name("/data0"), "testobj0")
    icn_repo0.repolayer.add_content(Name("/data0/somePath"), "testobj1")
    icn_repo0.repolayer.add_content(Name("/data0/somePath/deeperFolder"), "testobj2")