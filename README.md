# RadioSeed
A small python script to collect random entropy from a geiger counter connected to an RPi, and make BIP39 seeds.

Initially motivated by a tweet from @raw_avacado: https://twitter.com/raw_avocado/status/1433408813596545027

You can see this in operation here: https://twitter.com/Arceris_btc/status/1435692937153744898

Requires a Geiger Counter that provides pulse data. I used the MightyOhm Geiger Counter Kit https://mightyohm.com/blog/products/geiger-counter/

In this case, both the display and the geiger counter are entirely powered off the Raspberry Pi.

The geiger counter pulse is supplied to Pin #12 (GPIO 18), with power from pin 1 (+3.3v) and ground on pin 6.

Once all the dependencies are loaded, the Raspberry Pi can be totally disconnected from the network.

The initial code was adapted from https://apollo.open-resource.org/mission:log:2014:06:13:generating-entropy-from-radioactive-decay-with-pigi

While I've checked the outputs to ensure they are compliant (both in Sparrow and on https://iancoleman.io/bip39/), use at your own risk.
