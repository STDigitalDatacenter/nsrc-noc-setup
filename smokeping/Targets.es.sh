#!/bin/bash -eu

# Note that the generated config is different to Targets.en.sh

cat <<EOS
*** Targets ***

probe = FPing

menu = Top
title = Gráficos de Latencia de Red
remark = Gráficos de Latencia por Smokeping por el Taller \
         Gestión y Monitoreo de Redes

+Local

menu = Local Network Monitoring and Management
title = Local Network

++LocalMachine

menu = Local Machine
title = This host
host = localhost

#
# ********* Servidores del Taller **********
#

+NOCServers

menu = NOCServidor
title = Servidores de Gestion de Redes

++noc

menu = noc
title = NOC del Taller
host = noc.ws.nsrc.org
EOS

for x in {1..6}; do
cat <<EOS

#
# ******** Servidores Campus $x  ***********
#

+Campus${x}

menu = Servidores Campus $x
title = Servidores en Campus $x

++srv1

menu = srv1
title = Campus $x Servidor Compartido 1
host = srv1.campus${x}.ws.nsrc.org

++host1

menu = host1
title = Campus $x Servidor 1
host = host1.campus${x}.ws.nsrc.org

++host2

menu = host2
title = Campus $x Servidor 2
host = host2.campus${x}.ws.nsrc.org

++host3

menu = host3
title = Campus $x Servidor 3
host = host3.campus${x}.ws.nsrc.org

++host4

menu = host4
title = Campus $x Servidor 4
host = host4.campus${x}.ws.nsrc.org

++host5

menu = host5
title = Campus $x Servidor 5
host = host5.campus${x}.ws.nsrc.org

++host6

menu = host6
title = Campus $x Servidor 6
host = host6.campus${x}.ws.nsrc.org
EOS
done


for x in {1..6}; do
cat <<EOS

#
#******** Campus $x Dispositivos de Red ********
#

+campus${x}Network

menu = Dispositivos de Red Campus $x
title = Dispositivos de Red Campus $x

#
# ********** Campus $x Border Router *********
#

++border
menu = Borde
title = Enrutador de Borde

+++campus${x}
menu = campus${x}
title = Enrutador de Borde Campus $x
host = bdr1.campus${x}.ws.nsrc.org


#
# ********** Campus $x Enrutador Central *********
#

++core
menu = Central
title = Enrutador Central

+++campus${x}
menu = campus${x}
title = Enrutador Central Campus $x
host = core1.campus${x}.ws.nsrc.org

#
# ********** Campus $x conmutadores *********
#

++switches
menu = Conmutadores
title = Conmutadores de Distribucion

+++building1
menu = Edificio 1
title = Conmutador de Distribucion Campus $x Edificio 1
host = dist1-b1.campus${x}.ws.nsrc.org

+++building2
menu = Edificio 2
title = Conmutador de Distribucion Campus $x Edificio 2
host = dist1-b2.campus${x}.ws.nsrc.org
EOS
done

cat <<EOS



#
# CAMBIO DE PROBE (HTTP)
#


#
# Respuesta del servidor web local
#

+HTTP

menu = Respuesta Local HTTP
title = Respuesta HTTP PCs
EOS

for x in {1..6}; do
cat <<EOS

#
#******** Campus $x Respuesta de HTTP ********
#

++campus${x}HTTP

menu = Respuesta HTTP Campus $x
title = Respuesta HTTP Campus $x

+++srv1

menu = srv1
title = Tiempo de Respuesta a srv1 HTTP
probe = EchoPingHttp
host = srv1.campus${x}.ws.nsrc.org

+++host1

menu = host1
title = Tiempo de Respuesta host1 HTTP
probe = EchoPingHttp
host = host1.campus${x}.ws.nsrc.org

+++host2

menu = host1
title = Tiempo de Respuesta host1 HTTP
probe = EchoPingHttp
host = host2.campus${x}.ws.nsrc.org

+++host3

menu = host3
title = Tiempo de Respuesta host3 HTTP
probe = EchoPingHttp
host = host3.campus${x}.ws.nsrc.org

+++host4

menu = host4
title = Tiempo de Respuesta host4 HTTP
probe = EchoPingHttp
host = host4.campus${x}.ws.nsrc.org

+++host5

menu = host5
title = Tiempo de Respuesta host5 HTTP
probe = EchoPingHttp
host = host5.campus${x}.ws.nsrc.org

+++host6

menu = host6
title = Tiempo de Respuesta host6 HTTP
probe = EchoPingHttp
host = host6.campus${x}.ws.nsrc.org
EOS
done

cat <<EOS


#
# Muestra de Chequeo de DNS
#

+DNS

probe = DNS
menu = Demora DNS
title = Chequeos de Demora DNS

++LocalDNS1
menu = gw.ws.nsrc.org
title =  Demora DNS de Servidor DNS local en gw.ws.nsrc.org
host = gw.ws.nsrc.org

++GoogleA
menu = 8.8.8.8
title = Demora de DNS google-public-dns-a.google.com
host = google-public-dns-a.google.com

++GoogleB

menu = 8.8.4.4
title = Demora de DNS google-public-dns-b.google.com
host = google-public-dns-b.google.com

++OpenDNSA

menu = 208.67.222.222
title = Demora de DNS resolver1.opendns.com
host = resolver1.opendns.com

++OpenDNSB

menu = 208.67.220.220
title = Demora de DNS resolver2.opendns.com
host = resolver2.opendns.com


#
# Grafico MultiServidor de todos los chequeos de demora de DNS
#

++MultiHostDNS

menu = MultiServidor DNS
title = Respuestas DNS Consolidadas
host = /DNS/LocalDNS1 /DNS/GoogleA /DNS/GoogleB /DNS/OpenDNSA /DNS/OpenDNSB
EOS
