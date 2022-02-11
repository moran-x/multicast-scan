# multicast-scan

The script scans the udp multicast streams and gets the name of the channels using the m3 file

m3u file example
```
#EXTM3U
#EXTINF:-1, 239.1.1.10
udp://@239.1.1.10:1234
#EXTINF:-1, 239.1.1.11
udp://@239.1.1.11:1234
```

**The script works only in _unix_ and only on _udp_ streams.**