# Raspberry Pi 4 Sports Command Center

A full-screen HDMI monitor dashboard with rotating live sports scores, continuous ticker, headlines, Open-Meteo weather, NOAA space weather / ham-band estimates, local ADS-B aircraft status, local and UTC clocks, and a remote settings page.

## Install on Raspberry Pi OS Desktop

1. Copy this folder to the Pi, for example `/home/pi/sports-scoreboard`.
2. Open Terminal in the folder.
3. Run:

```bash
chmod +x scripts/install.sh
./scripts/install.sh
sudo reboot
```

The dashboard opens automatically in Chromium kiosk mode after desktop login.

## Remote settings

From a phone or PC on the same network, open:

`http://PI-IP-ADDRESS:8080/settings`

Find the Pi address with:

```bash
hostname -I
```

## ADS-B setup

In Settings, enter the URL that returns your feeder's `aircraft.json`. Common examples:

- `http://127.0.0.1/tar1090/data/aircraft.json` when the dashboard is installed on the feeder Pi.
- `http://adsb-feeder.local/tar1090/data/aircraft.json` for another Pi on the LAN.
- `http://PI-IP/dump1090-fa/data/aircraft.json` for some PiAware installs.

## Supported sports identifiers

`mlb`, `nfl`, `nba`, `nhl`, `wnba`, `ncaaf`, `ncaam`

The sports/news adapter uses ESPN's publicly reachable web JSON endpoints. They are unofficial and may change. Weather uses Open-Meteo; space weather uses NOAA SWPC. The app keeps running when an individual source is unavailable.

## Useful commands

```bash
sudo systemctl status sports-scoreboard
sudo systemctl restart sports-scoreboard
journalctl -u sports-scoreboard -f
```

Dashboard: `http://PI-IP:8080/`  
Settings: `http://PI-IP:8080/settings`
