# multicast-scan

Script scans udp multicast streams from m3u file

m3 file example
#EXTM3U
#EXTINF:-1, 239.1.1.10
udp://@239.1.1.10:1234
#EXTINF:-1, 239.1.1.11
udp://@239.1.1.11:1234


The script works only in unix and only on udp streams.