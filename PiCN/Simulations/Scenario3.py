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
    # ICN Forwarder 1
    icn_fwd1 = ICNForwarder(port=0, encoder=NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("icn1")],
                            log_level=255, ageing_interval=1)
    # ICN Forwarder 2
    icn_fwd2 = ICNForwarder(port=0, encoder=NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("icn2")],
                            log_level=255, ageing_interval=1)
    # ICN Forwarder 3
    icn_fwd3 = ICNForwarder(port=0, encoder=NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("icn3")],
                            log_level=255, ageing_interval=1)

    # PS PIT
    icn_fwd0.icnlayer.pit = synced_data_struct_factory.manager.pit(pub_sub=True)
    icn_fwd1.icnlayer.pit = synced_data_struct_factory.manager.pit(pub_sub=True)
    icn_fwd2.icnlayer.pit = synced_data_struct_factory.manager.pit(pub_sub=True)
    icn_fwd3.icnlayer.pit = synced_data_struct_factory.manager.pit(pub_sub=True)
    # PS Repos
    icn_repo0 = ICNDataRepositoryPubSub(foldername=None, prefix=Name("/data0"), port=0,
                                        interfaces=[simulation_bus.add_interface("repo0")], encoder=NdnTlvEncoder(),
                                        log_level=255)
    icn_repo1 = ICNDataRepositoryPubSub(foldername=None, prefix=Name("/data1"), port=0,
                                        interfaces=[simulation_bus.add_interface("repo1")], encoder=NdnTlvEncoder(),
                                        log_level=255)
    icn_repo2 = ICNDataRepositoryPubSub(foldername=None, prefix=Name("/data2"), port=0,
                                        interfaces=[simulation_bus.add_interface("repo2")], encoder=NdnTlvEncoder(),
                                        log_level=255)
    # Fetchtools
    fetch_tool_0 = Fetch("icn0", None, 255, NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("fetchtool0")],
                         face_id=0)
    fetch_tool_1 = Fetch("icn1", None, 255, NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("fetchtool1")],
                         face_id=1)
    fetch_tool_2 = Fetch("icn1", None, 255, NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("fetchtool2")],
                         face_id=2)


    # Manager to add Interfaces and FW-Rules
    mgmt_client0 = MgmtClient(icn_fwd0.mgmt.mgmt_sock.getsockname()[1])
    mgmt_client1 = MgmtClient(icn_fwd1.mgmt.mgmt_sock.getsockname()[1])
    mgmt_client2 = MgmtClient(icn_fwd2.mgmt.mgmt_sock.getsockname()[1])
    mgmt_client3 = MgmtClient(icn_fwd3.mgmt.mgmt_sock.getsockname()[1])

    # start everything
    icn_fwd0.start_forwarder()
    icn_fwd1.start_forwarder()
    icn_fwd2.start_forwarder()
    icn_fwd3.start_forwarder()

    icn_repo0.start_repo()
    icn_repo1.start_repo()
    icn_repo2.start_repo()
    simulation_bus.start_process()

    # interfaces the content is forwarded to
    mgmt_client0.add_face("repo0", None, 0)
    mgmt_client1.add_face("icn0", None, 0)
    mgmt_client1.add_face("icn2", None, 0)
    mgmt_client2.add_face("icn3", None, 0)
    mgmt_client2.add_face("repo1", None, 0)
    mgmt_client3.add_face("repo0", None, 0)
    mgmt_client3.add_face("repo2", None, 0)



    mgmt_client0.add_forwarding_rule(Name("/data0"), [0])
    mgmt_client1.add_forwarding_rule(Name("/data0"), [0,1])
    mgmt_client1.add_forwarding_rule(Name("/data1"), [1])
    mgmt_client1.add_forwarding_rule(Name("/data2"), [1])
    mgmt_client2.add_forwarding_rule(Name("/data0"), [0])
    mgmt_client2.add_forwarding_rule(Name("/data1"), [1])
    mgmt_client2.add_forwarding_rule(Name("/data2"), [0])
    mgmt_client3.add_forwarding_rule(Name("/data0"), [0])
    mgmt_client3.add_forwarding_rule(Name("/data2"), [1])


    name0 = Name("/data0/subscribe(3)")
    #fetch_tool_0.listen_for_content(name0)


    name1 = Name("/data1/subscribe(2)")
    #fetch_tool_1.listen_for_content(name1)

    name2 = Name("/data0/subscribe(10)")
    name3 = Name("/data1/subscribe(10)")
    name4 = Name("/data2/subscribe(10)")
    fetch_tool_2.listen_for_content(name2)
    #fetch_tool_2.listen_for_content(name3)
    #fetch_tool_2.listen_for_content(name4)


    time.sleep(3)
    icn_repo0.repolayer.add_content(Name("/data0/content0"), "testobj0")
    icn_repo1.repolayer.add_content(Name("/data1/content1/somePath1/someFolder1"), "testobj1")
    icn_repo2.repolayer.add_content(Name("/data2"), "testobj2")


