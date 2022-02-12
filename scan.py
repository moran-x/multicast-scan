# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""The script scans the udp multicast streams and gets the name of the channels using the m3 file.
  Created By:  Moran <moran.x@gmail.com>
  Version: 1.0.0
  Git: https://github.com/moran-x/multicast-scan
"""

import argparse
import json
import os
import platform
import re
import socket
import struct
import subprocess

parser = argparse.ArgumentParser(description='Script to check the IPTV UDP streams from m3u playlist')
parser.add_argument("--port", help="additional UDP port to scan. Default: 1234", required=False, default=1234)
parser.add_argument("--ip", help="additional IP to scan. Default: 239.1.1.10", required=False, default='239.1.1.10')
parser.add_argument("--info_timeout", help="Time to wait in seconds for the stream's info", required=False, default=10)
parser.add_argument("--udp_timeout", help="Time to wait in seconds for the UPD port reply", required=False, default=10)
parser.add_argument("--playlist", help="Playlist *.m3u file with UDP streams", required=False)


def get_ffprobe(address, port, info_timeout):
    """ To get the json data from ip:port
    :param address: stream ip address
    :param port: connection port
    :param info_timeout: Time to wait in seconds
    :return: channel name
    """

    # Run the ffprobe with given IP and PORT with a given timeout to execute
    try:
        # Capture the output from ffprobe
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_programs', f'udp://@{address}:{port}'],
            capture_output=True, text=True, timeout=info_timeout)
        # Convert the STDOUT to JSON
        json_string = json.loads(str(result.stdout))
    except Exception:
        print(f'[*] No data found for {address}:{port}')
        return 0
    # Parse the JSON "PROGRAMS" section

    for program in json_string['programs']:
        # Parse the JSON "STEAMS" section
        for stream in program['streams']:
            # Check the stream via index data
            try:
                # Check the stream's channel name
                try:
                    if program['tags']['service_name'] != '':
                        return program['tags']['service_name']
                    else:
                        print(f'[*] !!! No channel name found for {address}:{port} !!!')
                        return 1
                except Exception:
                    print(f'[*] !!! No channel name found for {address}:{port} !!!')
                    return 1
            except Exception:
                print(f'[*] No stream found for {address}:{port}')
                return 0


def check_udp_connectivity(url, timeout=None):
    """
    Trying to wake up udp thread
    :param url: IP address and port like 239.0.0.1:1234
    :param timeout: connection timeout
    :return: True or False
    """
    ipaddr, port = url.rsplit(':', 1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(timeout)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(('', int(port)))
    mreq = struct.pack('4sl', socket.inet_aton(ipaddr), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    try:
        if sock.recv(10240):
            return True
    except socket.timeout:
        pass
    return False


def playlist_parser(playlist):
    """ Function that returns a dictionary of UDP streams
    :param playlist: Full path to the playlist
    :return: Dictionary of UDP streams
    """

    # Defining regular expression for strings
    channel_name_re = re.compile(r'(?<=#EXTINF:-1,)(.*)(?=$)')
    channel_address_re = re.compile(r'(?<=@)(.*)(?=$)')

    # Create a dictionary
    dictionary = {}

    # Open the playlist file and write the data to the dictionary
    with open(playlist) as playlist:
        for counter, line in enumerate(playlist):
            if re.findall(channel_name_re, line):
                channel_name = re.search(channel_name_re, line).group()
                channel_address = re.search(channel_address_re, playlist.readline()).group()
                dictionary[channel_name] = channel_address

    return dictionary


def udp_ports_parser(channels):
    """ Function to get the list of the unique ports from the UDP channels dictionary
    :param channels: Dictionary of UDP streams
    :return: List of the unique ports
    """

    # Get the unique values of UDP channel:port lines
    upd_channels_ports = set(channels.values())

    # Get the list of UDP ports
    port_list = []
    for item in upd_channels_ports:
        port = item.split(':')[1]
        port_list.append(port)

    # Get the unique list of UDP ports
    port_list = set(port_list)

    return port_list


def create_file(playlist):
    """ Prepare the resulting playlist file
    :param playlist: Name of playlist
    :return: Full path to the playlist and Name
    """

    # define the current directory
    currentpath = os.path.dirname(os.path.realpath(__file__))

    # Define the playlist file name
    playlistfilename = f'{playlist.rsplit(".", 1)[0]}_name.m3u'
    playlistfile = os.path.join(currentpath, playlistfilename)

    # Open the playlist file and add the first line (header)
    with open(playlistfile, 'w') as file:
        file.write('#EXTM3U\n')

    return playlistfilename, playlistfile


def playlist_add(ip, port, name, playlistfile):
    """ Add the given IP and port to the playlist file
    :param ip: stream ip address
    :param port: Connection port
    :param name: Channel name
    :param playlistfile: full path to playlist file
    """

    # Check the name variable
    if type(name) is int:
        channel_string = f'#EXTINF:-1,Channel: {ip}:{port}\n'
    else:
        channel_string = f'#EXTINF:-1,{name}\n'

    # Open the file
    with open(playlistfile, 'a') as file:

        # Add the channel name line
        file.write(channel_string)

        # Add the channel address
        file.write(f'udp://@{ip}:{port}\n')


# If the playlist argument is specified
def action_playlist(playlist, info_timeout, udp_timeout):
    """ Parce playlist file and check ip:port and create new playlist
    :param playlist: playlist file
    :param info_timeout: time to wait in seconds for get INFO
    :param udp_timeout: time to wait in seconds for get UDP
    """
    # Create a resulting playlist file:
    playlistfilename, playlistfile = create_file(playlist)

    channels_dictionary = []

    # Check the input playlist file
    if not os.path.isfile(playlist):
        print('[*] Please specify the correct file!')
        exit()
    else:
        print(f'[*] Playlist file: {playlist}')

    # Get the dictionary of UDP channels
    channels_dictionary = playlist_parser(playlist)

    for k, v in channels_dictionary.items():
        ipaddr, port = v.rsplit(':', 1)

        # Trying to wake up the udp thread
        check_udp_connectivity(v, udp_timeout)
        info = get_ffprobe(ipaddr, port, info_timeout)
        if type(info) is int:
            print(v + ' - ' + ipaddr)
            playlist_add(ipaddr, port, ipaddr, playlistfile)
        else:
            print(v + ' - ' + info)
            playlist_add(ipaddr, port, info, playlistfile)


# Single IP and PORT check
def action_ip_port(ip, port, info_timeout, udp_timeout):
    """ Single IP and PORT check
    :param ip: IP multicast stream
    :param port: PORT multicast stream
    :param info_timeout: time to wait in seconds for get INFO
    :param udp_timeout: time to wait in seconds for get UDP
    """
    check_udp_connectivity(ip+':'+str(port), udp_timeout)
    info = get_ffprobe(ip, port, info_timeout)
    if type(info) is int:
        print(ip+':'+str(port) + ' - ' + ip)
    else:
        print(ip+':'+str(port) + ' - ' + info)


def main():
    """
    Mine function
    """
    # Define the script arguments as a <args> variable
    args = parser.parse_args()

    # Check the OS name
    os_name = platform.system()

    # Checking if the system is Unix base
    if os_name != 'Linux':
        print(f'[*] This script only works on Unix base systems. Your system is {os_name}')
        exit()

    # Check that ffprobe are installed
    try:
        subprocess.call(['ffprobe', '-v', 'quiet'])
    except FileNotFoundError:
        print('[*] ffprobe are not installed! Please install first: https://ffmpeg.org/')
        exit()

    # Single IP and PORT check
    if args.ip and args.port:
        action_ip_port(args.ip, args.port, args.info_timeout, args.udp_timeout)

    # If the playlist argument is specified
    if args.playlist:
        action_playlist(args.playlist, args.info_timeout, args.udp_timeout)


if __name__ == "__main__":
    main()
