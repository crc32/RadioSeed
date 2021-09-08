#!/usr/bin/env python
# entropy generating geigercounter
# Modified from https://apollo.open-resource.org/mission:log:2014:06:13:generating-entropy-from-radioactive-decay-with-pigi

 
import geiger
import time
import datetime
import textwrap
import binascii # for conversion between Hexa and bytes
import qrcode
import io, os
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44Coins, Bip44, Bip84, Bip32
from rich.console import Console, Group
from rich.table import Column, Table
from rich.progress import Progress
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print


class Bip39Generator(geiger.GeigerCounter):
    def __init__(self):
        #setup vars for randomness production
        self.toggle = False
        self.t0 = self.t1 = self.t2 = datetime.datetime.now()
        self.bitstring = ""
        self.bip39_bits = ""
        self.bip39_string = ""
        #self.bip39_entropy = ""
        self.bits = 256
        self.bip39_hex = ""
        self.mnemonic = ""
        self.xpub = ""
        self.zpub = ""
        self.keyFingerPrint = ""
        self.seed_timeout = 5 * 60
        self.qr_timeout = 60
        self.console = Console(record = True)
        self.make_file = False
 
        #call __init__ of superclass
        geiger.GeigerCounter.__init__(self)
 
 
    def tick (self,pin=0):
        # This works like this:
        # time:   |------------|-------------|-----------|-----------|
        # tick 0: t0
        # tick 1: t0           t1
        # tick 2: t2           t1            t0
        #                d0            d1
        # tick 3: t2                         t0          t1
        # tick 4:                            t2          t1          t0
        #                                          dO          d1
 
        self.tick_counter += 1
        if (self.tick_counter % 2) == 0:
            self.t2 = self.t0
            self.t0 = datetime.datetime.now()
            d0 = self.t1 - self.t2
            d1 = self.t0 - self.t1
 
            if d0 > d1:
                self.bitstring += "1" if self.toggle else "0"
            elif d0 < d1:
                self.bitstring += "0" if self.toggle else "1"
            else: #d0 = d1
                #print("Collision")
                1+1
 
            self.toggle = not self.toggle
 
        else:
            self.t1 = datetime.datetime.now()
 
    def generate_bip39(self,max_entropy):
        collected_entropy = 0
        #bar = IncrementalBar('Entropy', max=max_entropy)
        with Progress() as progress:

            task = progress.add_task("[green]Gathering Entropy...", total=max_entropy)
            while len(self.bip39_bits) <= max_entropy:
                if len(self.bitstring)>=8:
                    self.bip39_bits += self.bitstring[:8]
                    self.bitstring = self.bitstring[8:]
                    #bar.next(n=8)
                    progress.update(task, advance=8)
                else:
                    continue
                time.sleep(0.01)

        self.split_and_xor(max_entropy)
        self.calculate_keys()
        self.display_results()


    def split_and_xor(self,max_entropy):
        # If you collect enough extra entropy, we'll fold the extra over and XOR to generate
        # the 256 bits we need
        #
        num_split = max_entropy / self.bits
        working_bits = textwrap.wrap(self.bip39_bits, self.bits)
        # Discard any elements less than self.bytes (256)
        for x in working_bits:
            if len(x) < self.bits: continue
            if len(self.bip39_string) == 0:
                self.bip39_string = x
                continue
            self.bip39_string = ''.join('0' if i == j else '1' for i, j in zip(self.bip39_string,x))

        temp_bip39 = [self.bip39_string[i:i+8] for i in range(0, len(self.bip39_string), 8)]
        for x in temp_bip39:
            self.bip39_hex = self.bip39_hex + str(hex(int(x,2)))[2:].zfill(2)
        

    def calculate_keys(self):
        # Put the hex into a binary format for the mnemonic generation
        temp_bin = binascii.unhexlify(self.bip39_hex)

        # build mnemonic
        self.mnemonic = Bip39MnemonicGenerator().FromEntropy(temp_bin)

        # get the seed bytes to build the xpub and zpub
        seed_bytes = Bip39SeedGenerator(self.mnemonic).Generate()

        # Create bip32 and bip84 compliant base master keys
        bip32_ctx = Bip32.FromSeed(seed_bytes)
        bip84_mst_ctx = Bip84.FromSeed(seed_bytes, Bip44Coins.BITCOIN)

        # Store the bip32 Key Fingerprint (needed by Sparrow)
        self.keyFingerPrint = binascii.hexlify(bip32_ctx.FingerPrint())

        # select the correct bip84 branch key (m/84/0/0) for both bip84 and bip32
        bip84_acc_ctx = bip84_mst_ctx.Purpose().Coin().Account(0)
        bip32_ctx = bip32_ctx.DerivePath("84'/0'/0'")
        
        # Store the xpub and zpub
        self.xpub = bip32_ctx.PublicKey().ToExtended()
        self.zpub = bip84_acc_ctx.PublicKey().ToExtended()


    def display_results(self):
        phrase_array = self.mnemonic.split(" ")
        print("\n")
        

        phrase_table = Table(show_header=False, title="Seed Phrase", show_lines=True)
        phrase_table.add_column("1")
        phrase_table.add_column("2")
        phrase_table.add_column("3")
        phrase_table.add_column("4")
        phrase_table.add_column("5")
        phrase_table.add_row(
            "01.  " + phrase_array[0],
            "02.  " + phrase_array[1],
            "03.  " + phrase_array[2],
            "04.  " + phrase_array[3],
            "05.  " + phrase_array[4],
        )
        phrase_table.add_row(
            "06.  " + phrase_array[5],
            "07.  " + phrase_array[6],
            "08.  " + phrase_array[7],
            "09.  " + phrase_array[8],
            "10.  " + phrase_array[9],
        )
        phrase_table.add_row(
            "11.  " + phrase_array[10],
            "12.  " + phrase_array[11],
            "13.  " + phrase_array[12],
            "14.  " + phrase_array[13],
            "15.  " + phrase_array[14],
        )
        phrase_table.add_row(
            "16.  " + phrase_array[15],
            "17.  " + phrase_array[16],
            "18.  " + phrase_array[17],
            "19.  " + phrase_array[18],
            "20.  " + phrase_array[19],
        )
        phrase_table.add_row(
            "21.  " + phrase_array[20],
            "22.  " + phrase_array[21],
            "23.  " + phrase_array[22],
            "24.  " + phrase_array[23],
        )

        details_table = Table(show_header=False, title="Public Keys", show_lines=True)
        details_table.add_column("1",overflow="fold")
        details_table.add_row(
            "Key Fingerprint: " + str(self.keyFingerPrint),
        )
        details_table.add_row(
            "xpub: " + self.xpub,
        )
        details_table.add_row(
            "zpub: " + self.zpub,
        )

        os.system("clear")

        self.console.print(phrase_table)
        self.console.print(details_table)


        self.ProgressBar("Mnemonic & Pub Keys (Ctrl-C to end early): ", self.seed_timeout)

        # Build QR code of the Fingerprint & public keys.
        # For security, we do NOT include the mneumonic in the QR Code.
        qr = qrcode.QRCode(box_size=10, border=0, error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(self.xpub, optimize=50)
        xpub_qr = io.StringIO()
        qr.print_ascii(out=xpub_qr)
        xpub_qr.seek(0)
        qr.clear()
        qr.add_data(self.zpub, optimize=50)
        zpub_qr = io.StringIO()
        qr.print_ascii(out=zpub_qr)
        zpub_qr.seek(0)

        #layout["xpub"].update(

        xpub_table = Table(show_header=False, title="xPub Key", show_lines=True)
        xpub_table.add_column("1",overflow="fold")
        xpub_table.add_row(
            xpub_qr.read(),
        )

        zpub_table = Table(show_header=False, title="zPub Key", show_lines=True)
        zpub_table.add_column("1",overflow="fold")
        zpub_table.add_row(
            zpub_qr.read(),
        )

        self.console.print(xpub_table)
        self.ProgressBar("xpub (Ctrl-C to end early): ", self.qr_timeout)

        self.console.print(zpub_table)
        self.ProgressBar("zpub (Ctrl-C to end early): ", self.qr_timeout)

        if self.make_file: self.console.save_text("Last_Seed.txt")


    def ProgressBar(self, message, to):
        with Progress(transient=True) as progress:
            task = progress.add_task(message, total=to)
            i = 0
            try: 
                while(i < to):
                    progress.update(task, advance=1)
                    time.sleep(1)
                    i += 1
            except KeyboardInterrupt:
                pass
        os.system("clear")

    def GenerateFile(self, generate="N"):
        if generate == "Y" or generate == "y":
            self.make_file = True
            self.qr_timeout = 30
            self.seed_timeout = 30
        else:
            self.make_file = False


if __name__ == "__main__":
    keygen = Bip39Generator()
    print(Panel("Entropy needs to be collected in blocks of 256.\n" +
                "After collection, the values will be displayed on screen,\n" +
                "and a file will be generated (Last_Seed.txt) if you request it.\n" +
                "Saving as a file will reduce the on-screen display times to [green]30 seconds[white].\n" +
                "[red]IF YOU ALREADY HAVE A 'Last_Seed.txt' FILE, THIS WILL BE OVERWRITTEN IF YOU ANSWER YES![white]",
                title="Geiger Entropy Collection"))
    max_entropy = int(Prompt.ask("How much oversampling do you want (1x, 2x, &c.)")) * 256
    keygen.GenerateFile(Prompt.ask("Generate file (y/N)", default="N"))
    keygen.generate_bip39(max_entropy)
