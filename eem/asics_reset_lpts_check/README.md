This eem script is Python based and was developed specifically for a spitfire platform and tested with 7.3.3

1. Copy the script to a router's harddisk.

2. Add the script to router's eem repository using:

```
script add eem /harddisk:/ asics_reset_lpts_check_v1.0.py
```
3. Check the status of the script

```
show script status
```
4. Make a router has at least the following AAA confiugration

```
aaa authorization exec default local
aaa authorization eventmanager default local
aaa authentication login default local
```
5. Configure EEM event manager

```
event manager action asics_reset_lpts_check_action
 username cisco
 type script script-name asics_reset_lpts_check_v1.0.py maxrun seconds 3600 checksum sha256 d5c2676af611203cd844997c9660f191f0f06edba164945f3b7c1e97af4f668b
!
event manager policy-map asics_reset_lpts_check_policy
 trigger event asics_reset
 action asics_reset_lpts_check_action
!
event manager event-trigger asics_reset
 type syslog pattern ".*ASIC_ERROR_ACTION.*HARD_RESET"
!
```

Notes:

* Use a username, in this example: cisco, defined on the router.

* sha256 can be obtained by running the following command:

```
sha256sum /harddisk:/asics_reset_lpts_check_v1.0.py
```