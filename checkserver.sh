ADDR="127.0.0.1"
printf '>>Registering orestarod\n    '
wget -qO- http://$ADDR:5000/register/123/orestarod
printf '\n>>Registering airmper\n    '
wget -qO- http://$ADDR:5000/register/123/airmper
printf '\n>>orestarod joining tanalies\n    '
wget -qO- http://$ADDR:5000/join_group/tanalies/orestarod
printf '\n>>airmper joining tanalies\n    '
wget -qO- http://$ADDR:5000/join_group/tanalies/airmper
printf '\n>>listing tanalies members\n    '
wget -qO- http://$ADDR:5000/list_members/tanalies
printf '\n>>listing groups\n    '
wget -qO- http://$ADDR:5000/list_groups/
printf '\n>>orestarod quitting\n    '
wget -qO- http://$ADDR:5000/quit/0
printf '\n>>listing tanalies members\n    '
wget -qO- http://$ADDR:5000/list_members/tanalies
printf '\n>>airmper quitting\n    '
wget -qO- http://$ADDR:5000/quit/1
printf '\n>>listing all groups\n    '
wget -qO- http://$ADDR:5000/list_groups/
printf '\n'