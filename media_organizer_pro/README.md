# Media Organizer Pro

Objedinjeni GUI alat za organizaciju fotografija i videa te za pronalazak i
upravljanje duplikatima.

## Sto je spojeno

- Organizacija fotografija po datumu iz EXIF podataka ili datumu datoteke.
- Organizacija video datoteka po datumu iz FFprobe metapodataka ili datumu datoteke.
- Detekcija identicnih duplikata slika i videa pomocu SHA-256 hasha.
- Detekcija vizualno slicnih slika pomocu perceptual hasha.
- Opcionalna detekcija slicnih videa pomocu hasha video framea.
- Posebna NAS/video provjera: usporedba foldera za provjeru s referentnim folderima.
- Glavni jezik sucelja je engleski, a u headeru se moze prebaciti na hrvatski.
- Header ima PayPal donate gumb koji vodi na `https://paypal.me/danijel0304`.

## Pokretanje

```bash
cd media_organizer_pro
python3 media_organizer_pro.py
```

Ako koristite Windows, komanda moze biti:

```bash
python media_organizer_pro.py
```

## Ovisnosti

Program se moze pokrenuti sa standardnim `tkinter` modulom, ali za puni rad
preporucene su ovisnosti iz `requirements.txt`.

```bash
pip install -r requirements.txt
```

Za video datume preporucen je FFmpeg/FFprobe:

- Linux: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`
- Windows: instalirati FFmpeg i dodati ga u PATH

## Sigurnost

Organizacija po datumu je zadano postavljena na kopiranje, ne premjestanje.
Brisanje i premjestanje duplikata traze potvrdu prije akcije.

Prije rada nad velikom arhivom prvo testirajte na manjoj kopiji foldera.

## Glavne dorade u odnosu na stare skripte

- Jedan moderan GUI s tabovima umjesto vise odvojenih aplikacija.
- Zajednicke funkcije za skeniranje, hashiranje, datume i sigurno imenovanje.
- SHA-256 se cita u chunkovima, pa velike video datoteke ne pune memoriju.
- Vizualno trazenje slicnih slika vise ne ovisi o tome da datoteke imaju istu velicinu.
- Rezultati se nakon premjestanja ili brisanja ispravno uklanjaju iz tablica.
- Stare skripte nisu mijenjane; nova aplikacija je u zasebnom folderu.
