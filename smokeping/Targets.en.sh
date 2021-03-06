#!/bin/bash -eu
cat <<EOS
*** Targets ***

probe = FPing

menu = Top
title = Network Latency Grapher
remark = Smokeping Latency Grapher for Campus Network Design and Operations workshop

#
# ********* Classroom Servers **********
#

+Servers

menu = Servers
title = Network Management Servers

++noc

menu = noc
title = Workshop NOC
host = noc.ws.nsrc.org

++www

menu = www
title = Workshop WWW
host = www.ws.nsrc.org

#
# ******** Transit routers ***********
#

+transit

menu = Transit
title = Transit Routers

++transit1

menu = transit1.nren
title = transit1.nren
host = transit1.nren.ws.nsrc.org

++transit2

menu = transit2.nren
title = transit2.nren
host = transit2.nren.ws.nsrc.org

#
# ******** Campus routers ***********
#

+campus

menu = Campuses
title = Campuses

EOS
for x in {1..6}; do
cat <<EOS

++campus$x

menu = Campus $x
title = Campus $x

+++bdr1-campus$x

menu = bdr1.campus$x
title = bdr1.campus$x
host = bdr1.campus$x.ws.nsrc.org

+++srv1-campus$x

menu = srv1.campus$x HTTP
title = srv1.campus$x HTTP
probe = EchoPingHttp
host = srv1.campus$x.ws.nsrc.org
EOS
done

cat <<EOS

#
# Sample DNS probe
#

+DNS

probe = DNS
menu = DNS
title = DNS Latency Probes

++LocalDNS
menu = 100.64.0.1
title =  DNS Latency for 100.64.0.1
host = 100.64.0.1

++GoogleA
menu = 8.8.8.8
title = DNS Latency for 8.8.8.8 (google-public-dns-a.google.com)
host = 8.8.8.8

++GoogleB

menu = 8.8.4.4
title = DNS Latency for 8.8.4.4 (google-public-dns-b.google.com)
host = 8.8.4.4

EOS
