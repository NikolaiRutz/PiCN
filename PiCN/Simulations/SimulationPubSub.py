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
from PiCN.ProgramLibs.ICNDataRepository import ICNDataRepository

# TODO: ICN fw werden anscheinend nicht im BasicICNLayer aufgerufen
simulation_bus = SimulationBus(packetencoder=NdnTlvEncoder())

# ICN Forwarder 0
icn_fwd0 = ICNForwarder(port=0, encoder=NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("icn0")],
                        log_level=255, ageing_interval=1)
# ICN Forwarder 1
icn_fwd1 = ICNForwarder(port=0, encoder=NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("icn1")],
                        log_level=255, ageing_interval=1)
#TODO: repor erweitern für PS
ICNrepo = ICNDataRepository(foldername=None, prefix=Name("/data"), port=0,
                            interfaces=[simulation_bus.add_interface("repo0")])
# Manager to add Interfaces and FW-Rules
mgmt_client0 = MgmtClient(icn_fwd0.mgmt.mgmt_sock.getsockname()[1])
mgmt_client1 = MgmtClient(icn_fwd1.mgmt.mgmt_sock.getsockname()[1])

# Clients to fetch Data from Forwarder
fetch_tool_0 = Fetch("icn0", None, 255, NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("fetchtool0")])
fetch_tool_1 = Fetch("icn1", None, 255, NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("fetchtool1")])

icn_fwd0.start_forwarder()
icn_fwd1.start_forwarder()
simulation_bus.start_process()

# interfaces the content is forwarded to
mgmt_client0.add_face("icn1", None, 0)

# FW-Rule for Forwarder 0
mgmt_client0.add_forwarding_rule(Name("/data"), [0])
mgmt_client1.add_new_content(Name("/data/obj1"), "World")

name2 = Name("/data/obj1")
res2 = fetch_tool_0.fetch_data(name2, timeout=20)

print("Fetch_Tool_0: " + res2)

# create new Content/ put new content in queue
# wo wird diese Methode aufgerufen
content = Content(Name("/data/obj1"), "World")
icn_fwd0.icnlayer.queue_from_higher.put([0, content])
ICNrepo.repolayer.repo.add_content(Name("/data2"), "content")

icn_fwd0.stop_forwarder()
icn_fwd0.stop_forwarder()
fetch_tool_0.stop_fetch()
simulation_bus.stop_process()
mgmt_client0.shutdown()
mgmt_client1.shutdown()
