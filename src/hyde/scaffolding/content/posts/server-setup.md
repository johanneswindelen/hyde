author: Johannes
draft: False
date: 2021-03-01
type: posts
title: Server setup
urlstub: server-setup
---
# Ubuntu 18.04 basic server setup

Once your VPS is up and running, there are a few basic configuration changes necessary to 

a) make the server more secure and 
b) keep it secure over time.

We'll look at:

- creating a user account
- configuring SSH access
- configuring automatic updates
- enabling the firewall

## Create a user account

You should use an unprivileged account for most of your day-to-day activity. You may want to replace the username `joe` with something more meaningful for you.

`root@<server># adduser joe`

You may want to add this new user to the `sudo` group for sysadmin tasks

`root@<server># usermod -aG sudo joe`

Now, try logging in to your new user over SSH

`you@local$ ssh joe@<server>`

If all went well, you're now logged into the server and see

`joe@<server>$`

## Configure SSH access

Leaving SSH access open to the `root` user is considered a security hole. Let's shut that down by making the following changes

```
File: /etc/ssh/sshd_config
--
PermitRootLogin no 
```

## Configure Automatic Updates

Keeping the server up to date with security patches is a good idea. This configuration also sends out periodic emails to you, containing info about package upgrades.

`joe@<server>$ sudo apt install unattended-upgrades bsd-mailx`

You'll need to configure the `mailx` package - just pick the `Internet` option.

To enable unattended-upgrades:

`joe@<server>$ sudo dpkg-reconfigure -plow unattended-upgrades`

You'll want to hit `Yes` for automatic upgrades.

### Email status updates

Sending email updates for `unattended-upgrades` is simple!

```
File: /etc/apt/apt.conf.d/50unattended-upgrades
--
Unattended-Upgrade::Mail "your@emailaddress.com";
```

To make sure that `bsd-mailx` is configured correctly, `/etc/mailname` should contain a domain name that resolves to an IP address. This is important since some mailservers will check the origin address to ensure that the server actually exists. Gandi does:

```
Dec 21 21:54:51 <server> postfix/smtp[18154]: 9E0443E949: to=<sysadmin@example.com>, 
relay=spool.mail.gandi.net[217.70.178.1]:25, 
delay=0.35, 
delays=0.02/0.01/0.26/0.07, 
dsn=5.1.8, 
status=bounced (host spool.mail.gandi.net[217.70.178.1] said: 550 5.1.8 <root@<server>>: Sender address rejected: Domain not found (in reply to RCPT TO command))
```

TODO: check out exact email setup...

## Firewall

Setting up the `ufw` firewall is quick and simple!

`joe@<server>$ sudo ufw allow ssh`
`joe@<server>$ sudo ufw enable`


## Login alerts

```
Dec 25 06:50:04 jwserver sshd[20250]: Invalid user tshort from 92.222.94.46 port 44970
Dec 25 06:50:04 jwserver sshd[20250]: pam_unix(sshd:auth): check pass; user unknown
Dec 25 06:50:04 jwserver sshd[20250]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=92.222.94.46
Dec 25 06:50:05 jwserver sshd[20250]: Failed password for invalid user tshort from 92.222.94.46 port 44970 ssh2
Dec 25 06:50:05 jwserver sshd[20250]: Received disconnect from 92.222.94.46 port 44970:11: Bye Bye [preauth]
Dec 25 06:50:05 jwserver sshd[20250]: Disconnected from invalid user tshort 92.222.94.46 port 44970 [preauth]
Dec 25 06:50:11 jwserver kernel: [UFW BLOCK] IN=eth0 OUT= MAC=96:00:00:3a:5b:c6:d2:74:7f:6e:37:e3:08:00 SRC=51.161.12.231 DST=95.216.178.106 LEN=40 TOS=0x00 PREC
Dec 25 06:50:12 jwserver sshd[20260]: Invalid user linux from 65.98.111.218 port 32973
Dec 25 06:50:12 jwserver sshd[20260]: pam_unix(sshd:auth): check pass; user unknown
Dec 25 06:50:12 jwserver sshd[20260]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=65.98.111.218
Dec 25 06:50:14 jwserver sshd[20260]: Failed password for invalid user linux from 65.98.111.218 port 32973 ssh2
Dec 25 06:50:14 jwserver sshd[20260]: Received disconnect from 65.98.111.218 port 32973:11: Bye Bye [preauth]
Dec 25 06:50:14 jwserver sshd[20260]: Disconnected from invalid user linux 65.98.111.218 port 32973 [preauth]
Dec 25 06:50:18 jwserver sshd[20266]: Invalid user wordpress from 181.14.240.149 port 57739
Dec 25 06:50:18 jwserver sshd[20266]: pam_unix(sshd:auth): check pass; user unknown
Dec 25 06:50:18 jwserver sshd[20266]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=181.14.240.149
Dec 25 06:50:20 jwserver sshd[20266]: Failed password for invalid user wordpress from 181.14.240.149 port 57739 ssh2
Dec 25 06:50:20 jwserver sshd[20266]: Received disconnect from 181.14.240.149 port 57739:11: Bye Bye [preauth]
Dec 25 06:50:20 jwserver sshd[20266]: Disconnected from invalid user wordpress 181.14.240.149 port 57739 [preauth]
Dec 25 06:50:26 jwserver sshd[20277]: Invalid user sanjay from 34.73.39.215 port 35578
Dec 25 06:50:26 jwserver sshd[20277]: pam_unix(sshd:auth): check pass; user unknown
Dec 25 06:50:26 jwserver sshd[20277]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=34.73.39.215
Dec 25 06:50:28 jwserver sshd[20277]: Failed password for invalid user sanjay from 34.73.39.215 port 35578 ssh2
Dec 25 06:50:28 jwserver sshd[20277]: Received disconnect from 34.73.39.215 port 35578:11: Bye Bye [preauth]
Dec 25 06:50:28 jwserver sshd[20277]: Disconnected from invalid user sanjay 34.73.39.215 port 35578 [preauth]
Dec 25 06:50:33 jwserver kernel: [UFW BLOCK] IN=eth0 OUT= MAC=96:00:00:3a:5b:c6:d2:74:7f:6e:37:e3:08:00 SRC=202.51.84.52 DST=95.216.172.96 LEN=52 TOS=0x00 PREC=0
Dec 25 06:50:33 jwserver sshd[20286]: Invalid user nightwal from 52.157.192.40 port 1600
Dec 25 06:50:33 jwserver sshd[20286]: pam_unix(sshd:auth): check pass; user unknown
Dec 25 06:50:33 jwserver sshd[20286]: pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost=52.157.192.40
```

```
root@jwserver:/home/johannes# last
johannes pts/1        192.168.50.4     Wed Dec 25 06:50   still logged in
johannes pts/1        192.168.50.4     Wed Dec 25 06:48 - 06:49  (00:01)
johannes pts/0        76.103.62.251    Wed Dec 25 05:40   still logged in
johannes pts/0        50.250.255.107   Tue Dec 24 21:48 - 23:01  (01:12)
johannes pts/0        199.33.32.40     Tue Dec 24 03:39 - 04:05  (00:25)
johannes pts/0        76.103.62.251    Sun Dec 22 03:25 - 06:04  (02:38)
johannes pts/1        199.33.32.40     Sat Dec 21 22:08 - 22:18  (00:09)
johannes pts/2        199.33.32.40     Sat Dec 21 21:03 - 21:04  (00:00)
root     pts/0        199.33.32.40     Sat Dec 21 20:59 - 01:21  (04:22)
root     tty1                          Sat Dec 21 20:57   still logged in
reboot   system boot  4.15.0-72-generi Sat Dec 21 20:52   still running
```

This also gets triggered on, e.g. `scp`


```
File: /etc/ssh/sshrc
from: https://askubuntu.com/a/179924
---
ip=`echo $SSH_CONNECTION | cut -d " " -f 1`

logger -t ssh-wrapper $USER login from $ip
echo "User $USER just logged in from $ip" | mailx -s "SSH Login" -r sshd@johanneswindelen.com sysadmin@johanneswindelen.com &
```