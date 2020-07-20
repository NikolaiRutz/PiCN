from PiCN.ProgramLibs.Fetch import Fetch
from PiCN.ProgramLibs.NFNForwarder import NFNForwarder
from PiCN.Layers.LinkLayer.Interfaces import SimulationBus
from PiCN.Layers.LinkLayer.Interfaces import AddressInfo
from PiCN.Layers.PacketEncodingLayer.Encoder import BasicEncoder, SimpleStringEncoder, NdnTlvEncoder
from PiCN.Mgmt import MgmtClient
from PiCN.Packets import Content, Interest, Name


simulation_bus = SimulationBus(packetencoder=NdnTlvEncoder())
nfn_fwd0 = NFNForwarder(port=0, encoder=NdnTlvEncoder(),
                        interfaces=[simulation_bus.add_interface("nfn0")], log_level=255,
                        ageing_interval=1)

nfn_fwd1 = NFNForwarder(port=0, encoder=NdnTlvEncoder(),
                        interfaces=[simulation_bus.add_interface("nfn1")], log_level=255,
                        ageing_interval=1)

mgmt_client0 = MgmtClient(nfn_fwd0.mgmt.mgmt_sock.getsockname()[1])
mgmt_client1 = MgmtClient(nfn_fwd1.mgmt.mgmt_sock.getsockname()[1])

fetch_tool_0 = Fetch("nfn0", None, 255, NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("fetchtool0")])
fetch_tool_1 = Fetch("nfn0", None, 255, NdnTlvEncoder(), interfaces=[simulation_bus.add_interface("fetchtool1")])

nfn_fwd0.start_forwarder()
nfn_fwd1.start_forwarder()
simulation_bus.start_process()


mgmt_client0.add_face("nfn1", None, 0)
#FW Rule = FIB?
mgmt_client0.add_forwarding_rule(Name("/data"), [0])
#wo genau kommt PIT in der Simulation zum einsatz?
mgmt_client0.add_new_content(Name("/func/combine"), "Hello")


name1 = Name("/func/combine")
name2 = Name("/data/obj1")

fetch_tool_0.fetch_data("/subscribe(345435)")

res1 = fetch_tool_0.fetch_data(name1, timeout=20)
res2 = fetch_tool_0.fetch_data(name2, timeout=20)

#erstes fetch_tool bekommt ein NACK. Sollte im PUB/SUB content bekommen sobald aktualisiert?
mgmt_client1.add_new_content(Name("/data/obj1"), "World")

print("Fetch_Tool_0: " + res1 + res2)

res1 = fetch_tool_1.fetch_data(name2, timeout=20)
res2 = fetch_tool_1.fetch_data(name2, timeout=20)

print("Fetch_Tool_1: " + res1 + res2)



nfn_fwd0.stop_forwarder()
nfn_fwd1.stop_forwarder()
fetch_tool_0.stop_fetch()
simulation_bus.stop_process()
mgmt_client0.shutdown()
mgmt_client1.shutdown()
