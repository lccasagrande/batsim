#!/usr/bin/env python3

"""Generate an energy platform without network."""

import argparse


def generate_cluster_platform(nb_hosts, output_file,
                              set_epsilon=False):
    """Generate an energy homogeneous cluster platform."""

    # Information from Taurus.
    freqs = [
        {"freq": 2301000, "maxWatt": 203.12,"moyWatt": 190.738, "time": 28.2},
        {"freq": 2300000, "maxWatt": 180.5, "moyWatt": 171.02,  "time": 31.7},
        {"freq": 2200000, "maxWatt": 174.0, "moyWatt": 165.62,  "time": 33.7},
        {"freq": 2100000, "maxWatt": 169.25,"moyWatt": 160.47,  "time": 35.0},
        {"freq": 2000000, "maxWatt": 163.5, "moyWatt": 155.729, "time": 37.0},
        {"freq": 1900000, "maxWatt": 158.12,"moyWatt": 151.30,  "time": 38.9},
        {"freq": 1800000, "maxWatt": 153.88,"moyWatt": 146.92,  "time": 41.0},
        {"freq": 1700000, "maxWatt": 149.25,"moyWatt": 142.95,  "time": 43.6},
        {"freq": 1600000, "maxWatt": 145.25,"moyWatt": 138.928, "time": 46.4},
        {"freq": 1500000, "maxWatt": 141.0, "moyWatt": 135.368, "time": 48.1},
        {"freq": 1400000, "maxWatt": 137.5, "moyWatt": 132.519, "time": 56.3},
        {"freq": 1300000, "maxWatt": 133.5, "moyWatt": 128.87,  "time": 57.3},
        {"freq": 1200000, "maxWatt": 130.25,"moyWatt": 125.88,  "time": 62.7}
    ]
    maxx = freqs[0]["time"]
    for f in freqs:
        f["speed"] = 100.0 * maxx / f["time"]

    idle_watt = 95.0

    watt_off = 9.75
    time_on_to_off = 6.1
    watt_on_to_off = 616.08 / time_on_to_off
    time_off_to_on = 151.52
    watt_off_to_on = 18966.4228 / time_off_to_on

    speed_str = '{real_pstates}, {off}, {on_to_off}, {off_to_on}'.format(
        real_pstates=", ".join(['{s}Mf'.format(s=f["speed"]) for f in freqs]),
        off='1e-9Mf',
        on_to_off='{s}f'.format(s=1.0 / time_on_to_off),
        off_to_on='{s}f'.format(s=1.0 / time_off_to_on))

    pstate_id_off = len(freqs)
    pstate_id_on_to_off = pstate_id_off + 1
    pstate_id_off_to_on = pstate_id_off + 2

    sleep_pstates = '{off}:{on_to_off}:{off_to_on}'.format(
        off=pstate_id_off,
        on_to_off=pstate_id_on_to_off,
        off_to_on=pstate_id_off_to_on)

    wps = list()
    for f in freqs:
        if set_epsilon:
            wps.append('{idle}:{epsilon}:{moy}'
                       .format(idle=idle_watt,
                               epsilon=min(idle_watt*1.03,f["moyWatt"]),
                               moy=f["moyWatt"]))
        else:
            wps.append('{idle}:{moy}:{moy}'
                       .format(idle=idle_watt,
                               epsilon=min(idle_watt*1.03,f["moyWatt"]),
                               moy=f["moyWatt"]))
    wps.append('{off}:{off}:{off}'.format(off=watt_off))
    wps.append('{on_to_off}:{on_to_off}:{on_to_off}'
               .format(on_to_off=watt_on_to_off))
    wps.append('{off_to_on}:{off_to_on}:{off_to_on}'
               .format(off_to_on=watt_off_to_on))

    watt_per_state = ", ".join(wps)

    header = """<?xml version='1.0'?>
<!DOCTYPE platform SYSTEM "http://simgrid.gforge.inria.fr/simgrid/simgrid.dtd">
<platform version="4.1">

<AS id="AS0" routing="Full">
"""

    compute_cluster = """
    <cluster id="cluster_compute" prefix="host" suffix="" radical="0-{max_rad}"
             bw="125MBps" lat="50us" bb_bw="2.25GBps" bb_lat="500us"
             speed="{speed}">
        <!-- real pstates: {first_real_pstate} to {last_real_pstate}
             off: pstate: {off_pstate}
                  consumption: {off_watts} W
             shutdown: pstate: {on_to_off_pstate}
                       time: {on_to_off_time} s,
                       consumption: {on_to_off_watts} W
             boot: pstate: {off_to_on_pstate}
                   time: {off_to_on_time} s,
                   consumption: {off_to_on_watts} W
        -->
        <prop id="watt_per_state" value="{watt_per_state}" />

        <prop id="watt_off" value="{off_watts}" />

        <!-- OFF : ON->OFF (shutdown) : OFF->ON (booting) -->
        <prop id="sleep_pstates" value="{sleep_pstates}" />
    </cluster>
""".format(speed=speed_str,
           watt_per_state=watt_per_state,
           sleep_pstates=sleep_pstates,
           first_real_pstate=0, last_real_pstate=pstate_id_off - 1,
           off_pstate=pstate_id_off,
           on_to_off_pstate=pstate_id_on_to_off,
           off_to_on_pstate=pstate_id_off_to_on,
           on_to_off_time=time_on_to_off,
           off_to_on_time=time_off_to_on,
           off_watts=watt_off,
           on_to_off_watts=watt_on_to_off,
           off_to_on_watts=watt_off_to_on,
           max_rad=nb_hosts - 1)

    master_cluster = """
    <cluster id="cluster_master" prefix="master_host" suffix="" radical="0-0"
             bw="125MBps" lat="50us" bb_bw="2.25GBps" bb_lat="500us"
             speed="{speed}">
        <!-- real pstates: {first_real_pstate} to {last_real_pstate}
             off: pstate: {off_pstate}
                  consumption: {off_watts} W
             shutdown: pstate: {on_to_off_pstate}
                       time: {on_to_off_time} s,
                       consumption: {on_to_off_watts} W
             boot: pstate: {off_to_on_pstate}
                   time: {off_to_on_time} s,
                   consumption: {off_to_on_watts} W
        -->
        <prop id="watt_per_state" value="{watt_per_state}" />

        <prop id="watt_off" value="{off_watts}" />

        <!-- OFF : ON->OFF (shutdown) : OFF->ON (booting) -->
        <prop id="sleep_pstates" value="{sleep_pstates}" />
    </cluster>
""".format(speed=speed_str,
           watt_per_state=watt_per_state,
           sleep_pstates=sleep_pstates,
           first_real_pstate=0, last_real_pstate=pstate_id_off - 1,
           off_pstate=pstate_id_off,
           on_to_off_pstate=pstate_id_on_to_off,
           off_to_on_pstate=pstate_id_off_to_on,
           on_to_off_time=time_on_to_off,
           off_to_on_time=time_off_to_on,
           off_watts=watt_off,
           on_to_off_watts=watt_on_to_off,
           off_to_on_watts=watt_off_to_on)

    footer = """
    <link id="backbone" bandwidth="1.25GBps" latency="500us" />

    <ASroute src="cluster_compute" dst="cluster_master" gw_src="hostcluster_compute_router"
        gw_dst="master_hostcluster_master_router">
        <link_ctn id="backbone" />
    </ASroute>
</AS>
</platform>
"""

    output_file.write(header)
    output_file.write(compute_cluster)
    output_file.write(master_cluster)
    output_file.write(footer)
    output_file.close()


def main():
    """
    Program entry point.

    Parses the input arguments then calls generate_flat_platform.
    """
    parser = argparse.ArgumentParser(
        description='One-point-topology SimGrid platforms generator')

    parser.add_argument('--nb', '-n',
                        type=int,
                        help='The number of computing entities to create',
                        required=True)

    parser.add_argument('--output', '-o',
                        type=argparse.FileType('w'),
                        help="The output file to generate",
                        required=True)

    parser.add_argument('--set-epsilon', '-e',
                        action='store_true',
                        help='Whether the epsilon consumption should be given',
                        required=False)

    args = parser.parse_args()

    set_epsilon = False
    if args.set_epsilon:
        set_epsilon = True

    generate_cluster_platform(nb_hosts=args.nb,
                              output_file=args.output,
                              set_epsilon=set_epsilon)


if __name__ == "__main__":
    main()
