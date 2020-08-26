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

icn_fwd0.icnlayer.pit = synced_data_struct_factory.manager.pit(pub_sub=True)
icn_fwd1.icnlayer.pit = synced_data_struct_factory.manager.pit(pub_sub=True)
icn_fwd2.icnlayer.pit = synced_data_struct_factory.manager.pit(pub_sub=True)

icn_repo = ICNDataRepositoryPubSub(foldername=None, prefix=Name("/data"), port=0,
                                   interfaces=[simulation_bus.add_interface("repo0")], encoder=NdnTlvEncoder())
# Manager to add Interfaces and FW-Rules
mgmt_client0 = MgmtClient(icn_fwd0.mgmt.mgmt_sock.getsockname()[1])
mgmt_client1 = MgmtClient(icn_fwd1.mgmt.mgmt_sock.getsockname()[1])
mgmt_client2 = MgmtClient(icn_fwd2.mgmt.mgmt_sock.getsockname()[1])
mgmt_repo = MgmtClient(icn_fwd1.mgmt.mgmt_sock.getsockname()[1])

# Clients to fetch Data from Forwarder
fetch_tool_0 = Fetch("icn0", None, 255, NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("fetchtool0")])
fetch_tool_1 = Fetch("icn1", None, 255, NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("fetchtool1")])

icn_fwd0.start_forwarder()
icn_fwd1.start_forwarder()
icn_fwd2.start_forwarder()
icn_repo.start_repo()
simulation_bus.start_process()

# interfaces the content is forwarded to
mgmt_client0.add_face("icn1", None, 0)
mgmt_client0.add_face("icn2", None, 0)
mgmt_client1.add_face("repo0", None, 0)
mgmt_client2.add_face("repo0", None, 0)

# FW-Rules
mgmt_client0.add_forwarding_rule(Name("/data"), [0, 1])
mgmt_client1.add_forwarding_rule(Name("/data"), [0])
mgmt_client2.add_forwarding_rule(Name("/data"), [0])

# TODO: why mutiple interest packages goin to the repo?
name0 = Name("/data/obj1/subscribe(2)")
name1 = Name("/data/obj1/subscribe(2)")
# name2 = Name("/data/obj3/subscribe(1)")
#res0 = fetch_tool_0.fetch_data(name0, timeout=20)
res0 = fetch_tool_0.fetch_data(name1, timeout=20)
# res0 = fetch_tool_0.fetch_data(name2, timeout=20)


icn_repo.repolayer.add_content(Name("/data/obj1"), "content")

# TODO: content kommt zu spät an deswegen wird ein NACK ausgegeben
time.sleep(3)
print(res0)
# print("Fetch_Tool_0: " + res0)

# create new Content/ put new content in queue
# content = Content(Name("/data/obj1"), "World")
# icn_fwd0.icnlayer.queue_from_higher.put([0, content])

# Content dem Repo hinzufügen
# icn_repo.repolayer.repo.add_content(Name("/data/obj1"), "content")

icn_fwd0.stop_forwarder()
icn_fwd0.stop_forwarder()
fetch_tool_0.stop_fetch()
simulation_bus.stop_process()
mgmt_client0.shutdown()
mgmt_client1.shutdown()
