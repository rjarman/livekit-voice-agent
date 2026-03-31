## Deployment

- Clone the repo
- `cp .env.example .env` and change the required envs
- make sure these ports are open
```shell
sudo ufw allow 8000/tcp
sudo ufw allow 5060/udp
sudo ufw allow 10000:20000/udp
```
- run `docker compose up -d`
- goto http://<SERVER_IP_ADDRESS>:8000/sip-inbound and create inbound rule
```text
Trunk Name = <give a random name>
Phone Number = +8809666781580
```
create dispatch rule
```text
Rule Name = Route to Room
Trunk Ids = Select the previously created inbound rule
Dispatch Rule Type = Individual
Room Prefix = caller-
Agent Name = apple-seller-agent-bn
```
- goto http://<SERVER_IP_ADDRESS>:8000/sip-outbound and create outbound rule
```text
Trunk name = <give a random name>
Address = <SERVER_IP_ADDRESS>
Transport = udp
Numbers = <username number from bdcom>
Username = <username number from bdcom>
Password = <password number from bdcom>
```
- Minimum VM Requirements:
    - RAM 8GB
    - CORE 4
    - SSD 80GB
