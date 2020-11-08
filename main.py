MAX_CHIPS = 10


def CreatePetriNet(ps, Mas):
    Name = Mas[0]
    _Out = Mas[1]
    _In = Mas[2]
    ts[Name] = Transition(Name, [Out("p" + str(int(i) + 1), ps[int(i)]) for i in _Out.split(" ")],
                          [In("p" + str(int(i) + 1), ps[int(i)]) for i in _In.split(" ")])


def PrintGraph(graph):
    import networkx as nx
    import matplotlib.pyplot as plt
    G = nx.DiGraph()

    for edge in graph:
        one = edge[:edge.find(",")]
        two = edge[edge.find(",") + 1:]
        G.add_edge(one, two)

    nx.write_gml(G, 'graph.gml')
    nx.draw(G, with_labels=True, font_color='white', font_size=12, font_weight='bold')
    plt.show()


class Place:
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

    def fire(self):
        """
        Fire!
        """
        not_blocked = all(arc.non_blocking() for arc in self.out_arcs)
        # Note: This would have to be checked differently for variants of
        # petri  nets that take more than once from a place, per transition.
        if not_blocked:
            for arc in self.arcs:
                arc.trigger()
                # reachability_graph.append(str(self.name) + "," + str(arc.name))
        return not_blocked  # return if fired, just for the sake of debuging


class PetriNet:
    def __init__(self, transitions):
        """
        The petri net runner.
        :transitions: The transitions encoding the net.
        """
        self.transitions = transitions

    def run(self, firing_sequence, ps):
        """
        Run the petri net.
        Details: This is a loop over the transactions firing and then some printing.
        :firing_sequence: Sequence of transition names use for run.
        :ps: Place holdings to print during the run (debugging).
        """

        # print("Using firing sequence:\n" + " => ".join(firing_sequence))
        print("start {}\n".format([p.holding for p in ps]))
        prev_state = "t0"
        for name in firing_sequence:
            holdings = [p.holding for p in ps]
            for i in holdings:
                if i >= MAX_CHIPS:
                    raise (Exception("Increase in the number of chips in position p"
                                     + str(holdings.index(i) + 1)))
            t = self.transitions[name]
            if t.fire():
                if prev_state + "," + t.name not in reachability_graph:
                    reachability_graph.append(prev_state + "," + t.name)
                if t.name not in triggered_tr:
                    triggered_tr.append(t.name)
                prev_state = t.name
                print("{} fired!".format(name))
                print("  =>  {}".format([p.holding for p in ps]))
            else:
                # print("{} ...fizzled.".format(name))
                pass

        if set(list(ts.keys())).issubset(triggered_tr):
            print("All transitions worked!")
        else:
            print("\033[31m\nUnreachable transitions: " + str(set(list(ts.keys())) - set(triggered_tr)) + "\n")

        # print("\nfinal {}".format([p.holding for p in ps]))


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
    # parser.add_argument('--firings', type=int)
    parser.add_argument('--marking', type=int, nargs='+')
    return parser


if __name__ == "__main__":
    args = make_parser().parse_args()

    ps = [Place(m) for m in args.marking]
    with open('Network Configuration', 'r') as f:
        lines = f.read().splitlines()

    ts = dict()
    [CreatePetriNet(ps, InputDataParser(lines[i])) for i in range(len(lines))]

    firing_sequence = list(ts.keys()) * 100

    triggered_tr = list()
    reachability_graph = list()
    petri_net = PetriNet(ts)
    petri_net.run(firing_sequence, ps)
    PrintGraph(reachability_graph)
    # print(reachability_graph)
