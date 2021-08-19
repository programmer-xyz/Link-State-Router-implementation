import sys
from collections import defaultdict
from router import Router
from packet import Packet
from json import dumps, loads
from dijkstar import Graph, find_path


class LSrouter(Router):
    """Link state routing protocol implementation."""

    def __init__(self, addr, heartbeatTime):
        """TODO: add your own class fields and initialization code here"""
        Router.__init__(self, addr)  # initialize superclass - don't remove
        self.heartbeatTime = heartbeatTime
        self.last_time = 0
        self.list_check = []
        self.link_state = {}
        self.graph=Graph(undirected=True)
        self.router_list = []
        self.seq_num_dict = {}
        self.seqno = 0
        self.router_tracer = {}
        self.message_sent_check = False
        
    def broadcast(self, message):
        '''hy'''
        for link in self.link_state:
            make_packet = Packet(Packet.ROUTING,self.addr,link,message)
            self.send(self.link_state[link]['port'],make_packet)

    def handlePacket(self, port, packet):
        """TODO: process incoming packet"""
        if packet.isTraceroute():

            self.router_tracer[port] = packet
            dst_address = packet.dstAddr
            next_hop = []
            src_address = packet.srcAddr

            try:

                path=find_path(self.graph,self.addr,dst_address)
                next_hop.append(path)
                port_test = False
                _hop_found = False
                next_hop = path.nodes[1]

                sent = [self.link_state[link]['port'] for link in self.link_state if link == next_hop]
                sending = sent[0]

                if port_test:
                    port_test = False

                self.send(sending,packet)

            except:
                pass
        else:

            src_address = packet.srcAddr
            exist = self.status_seq_num(src_address)


            if exist == 0:
                extract = packet.getContent()

                data_recv = loads(extract)

                _key_list = list(self.link_state.keys())
                seq_number = data_recv['seqno']
                test_seq_num = False


                self.seq_num_dict[src_address] = seq_number
                #check seq num
                if seq_number > self.seq_num_dict[src_address]:
                    if not test_seq_num:
                        test_seq_num = True

                # send to all but person who sent
                for curr_addr in self.link_state:
                    if curr_addr == src_address:
                        continue

                    if curr_addr != src_address:
                        self.send(self.link_state[curr_addr]['port'],packet)


                curr_links = data_recv['neighbors']
                # if new node add it
                self.link_maker(src_address, curr_links)

                graph_data = self.graph.get_data()
                current_babygraph = graph_data[src_address]
                # to rem extra pple added in linkmaker
                self.duplicity_remover(current_babygraph, curr_links, src_address)

            if exist == 1:
                extract = packet.getContent()
                data_recv = loads(extract)
                seq_number = data_recv['seqno']

                seq_num_test = False
                if seq_number>self.seq_num_dict[src_address]:
                    seq_num_test = True

                if seq_num_test:

                    self.seq_num_dict[src_address] = seq_number

                    for curr_addr in self.link_state:
                        if curr_addr == src_address:
                            continue

                        if curr_addr != src_address:
                            self.send(self.link_state[curr_addr]['port'],packet)


                    curr_links = data_recv['neighbors']


                    self.link_maker(src_address, curr_links)

                    graph_data = self.graph.get_data()

                    current_babygraph = graph_data[src_address]

                    self.duplicity_remover(current_babygraph, curr_links, src_address)

    def link_maker(self, src_address, curr_links):
        '''hy'''
        for link in curr_links:
            self.graph.add_edge(src_address, link, curr_links[link]['cost'])

    def duplicity_remover(self, current_subgraph, curr_links, sender_address):
        '''hy'''
        extra_pple = [nodes for nodes in current_subgraph if nodes not in curr_links]

        for key in extra_pple:
            self.graph.remove_edge(sender_address,key)

    def handleNewLink(self, port, endpoint, cost):
        """TODO: handle new link"""

        self.graph.add_edge(self.addr, endpoint, cost)
        mini = {'port':port,'cost':cost}

        self.link_state[endpoint] = mini
        num = self.seqno + 1
        self.seqno= num
        # neighbours is a dictionary of port and cose

        message = dumps({'seqno':self.seqno, 'neighbors':self.link_state})
        self.broadcast(message)

    def send_trace(self, dst_address, packet):
        '''hy'''
        next_hop = []
        path=find_path(self.graph,self.addr,dst_address)
        next_hop.append(path)
        port_test = False
        _hop_found = False
        next_hop = path.nodes[1]

        for key in self.link_state:
            if key==next_hop:
                port_test = True
                sending_port = self.link_state[key]['port']

        if port_test:
            port_test = False

        self.send(sending_port,packet)


    def handleRemoveLink(self, port):
        """TODO: handle removed link"""

        rem_point = self.link_finder(port)

        self.graph.remove_edge(self.addr, rem_point)
        self.seqno = self.seqno + 1
        del self.link_state[rem_point]
        message = dumps({'seqno':self.seqno, 'neighbors':self.link_state})
        self.broadcast(message)

    def status_seq_num(self, sender_addr):
        '''hy'''
        exist = 0
        for curr_addr in self.seq_num_dict:
            if curr_addr == sender_addr:
                exist = 1
        return exist
    
    def link_finder(self,port):
        '''hy'''
        ans = [link for link in self.link_state if self.link_state[link]['port']==port]
        ret = ans[0]
        return ret

    def handleTime(self, timeMillisecs):
        """TODO: handle current time"""
        if timeMillisecs - self.last_time >= self.heartbeatTime:
            self.last_time = timeMillisecs
            self.message_sent_check = True
            num = self.seqno + 1
            _timer_control = False
            self.seqno = num

            message = dumps({'seqno':self.seqno, 'neighbors':self.link_state})
            self.broadcast(message)

    def debugString(self):
        """TODO: generate a string for debugging in network visualizer"""
        return ""
