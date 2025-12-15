# PioneerOS
a custom build linux image, for getting it up and running on a raspberry Pi system

step 1 :
sudo apt-get install -y \
    sed make binutils build-essential gcc g++ bash patch \
    gzip bzip2 perl tar cpio unzip rsync file bc wget \
    libncurses5-dev git

well , there was an issue in this implemntation, because , as far as I did undestand, it needs to be in the root file of the system, so that It could function( I assume ) , Thus , this repo , will be in the format of tutorial , of rebuilding this exact implmentation of this system. Maight be just a "fancy Readme tutorial style" 

aftre running the configure buildrro robot .sh file , I get to run this , to be configure the implmentation of the wifi ssid
(base) walid@MR-HP:~/buildroot$ sudo gedit board/raspberrypi/overlay/etc/wpa_supplicant.conf

