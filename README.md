## MehDNS Backend

🚧 Work-in-progress 🚧

A self hosted DDNS server built on Django REST Framework made to work with multiple DNS providers

Working DNS Backends

- [x] Technitium DNS Server
- [ ] Cloudflare (Work-in-progress)
- [ ] PowerDNS (Drawing board for now)

acme.sh support is planned for Let's Encrypt certificates

Templated from [DRF-Template](https://github.com/lemeow125/DRF_Template)

### Setup

Use the provided `docker-compose.yml` in this repository. Set `DEBUG` to `False` and populate the `.env` file with your SMTP/email provider and credentials.

Setup assumes you have your own DNS provider set up externally. See [setup](documentation/setup/README.md) for more info

#### External Database

MehDNS uses SQLite by default. To change this, specify an alternative value for `DB_TYPE` in your `.env`.

MehDNS will run any database backend that Django supports, mainly MySQL, PostgreSQL.

### Development

- Create a copy of the `.env.sample` file and name it as `.env` in the same directory
- Populate .env with values
- Run `docker-compose -f docker-compose.dev.yml up`

When using `docker-compose.dev.yml`, the entire project directory is mounted onto the container allowing for hot-reloading. This requires `DEBUG` to be set to `True`.

- [Inbucket](http://localhost:8025) (Local SMTP server)
- [Django Silk](http://localhost:8000/api/v1/silk) (For debugging/performance profiling)

### API

An OpenAPI page is available at [http://localhost:8000/api/v1/swagger](http://localhost:8000/api/v1/swagger)
