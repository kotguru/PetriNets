MAX_CHIPS = 10


def CreatePetriNet(ps, Mas):
    Name = Mas[0]
    _Out = Mas[1]
    _In = Mas[2]
    ts[Name] = Transition(Name, [Out("p" + str(int(i) + 1), ps[int(i)]) for i in _Out.split(" ")],
                          [In("p" + str(int(i) + 1), ps[int(i)]) for i in _In.split(" ")])


class Position:
    def __init__(self, holding):
        """
        Place vertex in the petri net.
        :holding: Numer of token the place is initialized with.
        """
        self.holding = holding


class ArcBase:
    def __init__(self, name, place, amount=1):
        """
        Arc in the petri net.
        :place: The one place acting as source/target of the arc as arc in the net
        :amount: The amount of token removed/added from/to the place.
        """
        self.name = name
        self.place = place
        self.amount = amount


class Out(ArcBase):
    def trigger(self):
        """
        Remove token.
        """
        self.place.holding -= self.amount

    def non_blocking(self):
        """
        Validate action of outgoing arc is possible.
        """
        return self.place.holding >= self.amount


class In(ArcBase):
    def trigger(self):
        """
        Add tokens.
        """
        self.place.holding += self.amount


class Transition:
    def __init__(self, name, out_arcs, in_arcs):
        """
        Transition vertex in the petri net.
        :out_arcs: Collection of ingoing arcs, to the transition vertex.
        :in_arcs: Collection of outgoing arcs, to the transition vertex.
        """
        self.name = name
        self.out_arcs = set(out_arcs)
        self.arcs = self.out_arcs.union(in_arcs)

    def might_work(self):
        not_blocked = all(arc.non_blocking() for arc in self.out_arcs)
        return not_blocked

    def fire(self):
        """
        Fire!
        """
        not_blocked = self.might_work()
        if not_blocked:
            for arc in self.arcs:
                arc.trigger()
        return not_blocked


class PetriNet:
    def __init__(self, transitions):
        """
        The petri net runner.
        :transitions: The transitions encoding the net.
        """
        self.transitions = transitions

    def trans_list(self):
        transition_list = list()
        for name in firing_sequence:
            if self.transitions[name].might_work():
                transition_list.append(name)
        return transition_list

    def run(self, ps):
        """
        Run the petri net.
        Details: This is a loop over the transactions firing and then some printing.
        :firing_sequence: Sequence of transition names use for run.
        :ps: Place holdings to print during the run (debugging).
        """
        global cur_mark
        print("start {}\n".format(get_markings(ps)))

        while len(future_marking) > 0:
            trans_flag = True
            cur_mark = future_marking[0]
            while trans_flag and cur_mark not in worked_positions:
                worked_positions.append(cur_mark)
                restore_markings(cur_mark)
                transition_list = self.trans_list()
                if len(transition_list) == 1:
                    t_name = transition_list[0]
                    self.transitions[t_name].fire()
                    new_mark = get_markings(ps)
                    print("{} fired!".format(t_name))
                    print("{}  =>  {}".format(cur_mark, new_mark))
                    links_num = len(reachability_graph)
                    reachability_graph.append([])
                    reachability_graph[links_num].append(cur_mark)
                    reachability_graph[links_num].append(new_mark)
                    reachability_graph[links_num].append(int(t_name[1]) + 1)
                    cur_mark = new_mark
                else:
                    if len(transition_list) > 1:
                        for i in range(1, len(transition_list)):
                            t_name = transition_list[i]
                            self.transitions[t_name].fire()
                            new_mark = get_markings(ps)
                            future_marking.append(new_mark)
                            print("Many transitions can work {}".format(t_name))
                            print("{}  =>  {}".format(cur_mark, new_mark))
                            links_num = len(reachability_graph)
                            reachability_graph.append([])
                            reachability_graph[links_num].append(cur_mark)
                            reachability_graph[links_num].append(new_mark)
                            reachability_graph[links_num].append(int(t_name[1]))
                        t_name = transition_list[0]
                        restore_markings(cur_mark)
                        self.transitions[t_name].fire()
                        new_mark = get_markings(ps)
                        print("{} fired!".format(t_name))
                        print("{}  =>  {}".format(cur_mark, new_mark))
                        links_num = len(reachability_graph)
                        reachability_graph.append([])
                        reachability_graph[links_num].append(cur_mark)
                        reachability_graph[links_num].append(new_mark)
                        reachability_graph[links_num].append(int(t_name[1]))
                        cur_mark = new_mark
                    else:
                        trans_flag = False
            future_marking.pop(0)

        if cur_mark not in worked_positions:
            worked_positions.append(cur_mark)


def InputDataParser(in_str):
    name = in_str[:2]
    start_out = in_str.find(":")
    end_out = in_str.find(">")
    start_in = end_out + 2

    return [name, in_str[start_out + 2: end_out - 2], in_str[start_in:]]


def make_parser():
    """
    :return: A parser reading in some of our simulation paramaters.
    """
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--marking', type=int, nargs='+')
    return parser


def get_markings(ps):
    return [p.holding for p in ps]


def restore_markings(marking):
    i = 0
    for pos in ps:
        pos.holding = marking[i]
        i += 1
    pass


def PrintGraph():
    import networkx as nx
    import matplotlib.pyplot as plt

    graph = nx.DiGraph()
    for i in range(len(reachability_graph)):
        graph.add_edges_from(
            [(', '.join(map(str, reachability_graph[i][0])), ', '.join(map(str, reachability_graph[i][1])))],
            weight=reachability_graph[i][2])

    edge_labels = dict([((u, v,), d['weight'])
                        for u, v, d in graph.edges(data=True)])
    pos = nx.spring_layout(graph)
    plt.figure(figsize=(20, 20))
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels)
    nx.draw(graph, pos, edge_cmap=plt.cm.Reds,
            node_size=500,
            font_size=12,
            with_labels=True)
    x_values, y_values = zip(*pos.values())
    x_max = max(x_values)
    x_min = min(x_values)
    x_margin = (x_max - x_min) * 0.25
    plt.xlim(x_min - x_margin, x_max + x_margin)
    plt.savefig("reach_graph.png")


if __name__ == "__main__":
    args = make_parser().parse_args()

    ps = [Position(m) for m in args.marking]
    with open('Network Configuration', 'r') as f:
        lines = f.read().splitlines()

    ts = dict()
    [CreatePetriNet(ps, InputDataParser(lines[i])) for i in range(len(lines))]

    firing_sequence = list(ts.keys())

    future_marking = list()
    future_marking.append(get_markings(ps))
    worked_positions = list()
    reachability_graph = list()

    petri_net = PetriNet(ts)
    petri_net.run(ps)
    PrintGraph()
