# bobydo.pro

## DNS Configuration

Cloudflare Email Routing setup for bobydo.pro.

![DNS Configuration](./dns-config.png)

### Records

| Type | Name | Content | TTL |
|------|------|---------|-----|
| MX | bobydo.pro | route1.mx.cloudflare.net (priority 14) | 1 hr |
| MX | bobydo.pro | route2.mx.cloudflare.net (priority 28) | 1 hr |
| MX | bobydo.pro | route3.mx.cloudflare.net (priority 42) | 1 hr |
| TXT | bobydo.pro | v=spf1 include:_spf.mx.cloudflare.net ~all | 1 hr |

### Nameservers

- lamar.ns.cloudflare.com
- laura.ns.cloudflare.com
