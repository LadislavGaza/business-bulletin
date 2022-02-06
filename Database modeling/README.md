# RPG DATABÁZA

Datábaza umožňuje implementáciu online RPG hry hranej na 2D ploche. Hru je možné rozšírovať o nové predmety, úlohy, mobov, bossov, profesie a schopnosti postáv a taktiež rozšírovať mapu o nové body a oblasti, z ktorých každá môže mať v sebe bossa oblasti.

## players
Táto tabuľka obsahuje záznamy pre všetkých registrovaných hráčov. Medzi registračné možnosti patrí registrácia pomocou mailovej adresy, cez Facebook a cez Google. Pri každom hráčovi sa zobrazuje jeho aktuálny status - či je online, offline alebo online a neaktívny (away). Ďalej obsahuje referenciu na id tímu hráča. Pokiaľ hráč nepatrí do žiadneho tímu, je táto referencia null.

Ak hráč zmaže svoj účet, vyplní sa stĺpec *deleted_at* na to, aby bolo možné ponechať záznam účtu po dobu 30 dní v prípade, že sa hráč rozhodne svoj účet obnoviť.

## player_invitations
Hráči vedia byť priatelia a taktiež sa môžu zoskupovať do tímov. Priateľstvo a účasť v tíme je na pozvánku, ktorá môže byť prijatá alebo zamietnutá. Pred rozhodnutím hráča, ktorý dostal pozvánku má táto pozvánka stav nastavený na "pending". To, či sa jedná o pozvánku o priateľstvo alebo tímovú pozvánku určuje hodnota *type*. Ak sa jedná o tímovú pozvánku tak hráč, ktorý túto pozvánku príjme je zaregistrovaný do tímu odosielateľa.

## player_friend_list
Obsahuje záznamy o priateľoch hráča.

## player_ignore_list
Obsahuje záznamy o hráčoch, ktorých sa rozhodol daný hráč ignorovať.

## player_messages
Obsahuje správy, ktoré si hráči medzi sebou poslali.

## teams
Obsahuje všetky tímy hráčov. Tím nemá vedúceho a zaniká ak z neho všetci hráči odídu.

## team_messages
Podobná ako player_messages, no správa sa zobrazí všetkým hráčom patriacim do tímu, ktorému je správa určená.

## characters
Obsahuje všetky vytvorené postavy. Tieto postavy majú meno, povolanie, level, celkové exp body, počet životov, počet many na používanie schopností, útočné a obranné číslo a bod na mape, na ktorom sa práve nachádzajú. Na rozlíšenie celkového počtu života a many od aktuálneho života a many má celkový počet predponu *base*.

## classes
Obsahuje povolania, ktorými môže postava byť. Jedna postava má jedno povolanie, ku ktorému sa viažu vlastné schopnosti. Každé povolanie sa pri zvýšení levelu správa rozdielne a preto má rôzne multipliers na zvýšenie života, many, útoku a obrany postavy. Napríklad mágovi sa pri zvýšení levelu zdvojnásobí mana.

## character_spells
Predstavuje asociačnú tabuľku medzi postavami a schopnosťami, ktoré získali. Každá schopnosť má level, ktorý určuje jej silu.

## spells
Obsahuje schopnosti, ktoré môže postava nadobudnúť. Niektoré schopnosti sa viažu pomocou *class_id* na určité povolanie, no tie ktoré nemajú toto políčko vyplnené môžu získať všetky postavy. Pri každej schopnosti je cena many na použitie *mana_cost* a levelové obmedzenie *required_level*, ktoré určuje od ktorého levelu je možné túto schopnosť získať.

## previous_spells
Na získanie niektorých schopností je nutné mať odomknuté predošlé schopnosti. Táto tabuľka určuje, ktoré schopnosti potrebuje postava mať, aby bola odomknutá iná schopnosť.

## character_items
Predstavuje asociačnú tabuľku medzi postavami a predmetmi, ktoré získali. Stĺpec *amount* určuje koľkokrát danú vec postava má a *equipped* určuje či ju má aktuálne na sebe.

## items
Obsahuje všetky herné predmety. Každý predmet je nejakého typu, napríklad helma alebo meč a pridáva hráčovi rozdielne bonusy.

## item_types
Obsahuje všetky typy predmetov v hre a informáciu o tom, či si ho postava môže nasadiť na seba.

## character_quests
Predstavuje asociačnú tabuľku medzi postavami a ich úlohami. Stĺpec *completed* označuje, či postava danú úlohu splnila.

## quests
Obsahuje herné úlohy, ktoré môžu postavy plniť. Úlohy sú levelovo obmedzené, počínajúc od levelu 1. Každá sa začína na nejakom bode na mape a taktiež musí mať exp odmenu za splnenie. Niektoré môžu mať za odmenu aj nejaký predmet.

## quest objectives
Táto tabuľka existuje na definovanie podmienok na splnenie úlohy. Podmienka hovorí o tom, koľko predmetov má postava nazbierať, poprípade koľko mobov nejakého druhu má zabiť. Úloha sa považuje za splnenú ak boli splnené aj všetky jej podmienky.

Jedna úloha môže mať pridelený ľubovoľný počet podmienok na splnenie. Pre zaručenie rozmanitosti hry je najlepšie, keď sa tieto podmienky neopakujú vo viacerých questoch a referencujú sa iba na jeden, aby mal každý quest svoje unikátne podmienky.

## character_progress
Je určená na zaznamenanie plnenia podmienok úlohy pre postavy. Pri nabraní úlohy sa postave do tejto tabuľky uložia podmienky na splnenie a počas zbierania predmetov alebo zabíjania mobov sa aktualizuje *amount* - počet nazbieraných predmetov alebo zabitých mobov.

## mobs
Obsahuje herných mobov, s ktorými sa hráč môže stretnúť. Base atribúty mobov sa upravujú podľa toho, s akým levelom hráča sa stretávajú. Mob môže byť taktiež boss. Podľa toho sa dá nastaviť ako sa mob správa, napríklad bossovia nemôžu opúšťať svoje políčko alebo nebudú mať upravované atribúty podľa levelu hráča.

Za zabitie každého moba dostáva postava exp body. Koľko ich dostane tiež v konečnom dôsledku určuje level postavy.

## loot_items
Pri zabití moba môžu hráči dostať predmety. Táto tabuľka určuje, aké predmety môžu padať z rozdielnych mobov.

## spawn_requirements
Na to, aby sa mob zjavil vo svete potrebuje mať hráč splnené podmienky, napríklad dokončené nejaké úlohy alebo zabitého moba iného druhu a taktiež dosiahnutý potrebný level.

## spawned_mobs
Títo mobovia predstavujú tých, ktorí sa zjavili hráčom a pohybujú sa vo svete. Obsahuje referenciu na hráčov, ktorí ho môžu vidieť a bod na ktorom sa nachádza. Jeho base atribúty sú upravené podľa levelu hráča, ktorému sa pôvodne zjavil.

## areas
Herná mapa je rozdelená na územia, ktoré sú levelovo obmedzené (na obrázku rozlíšené farbami). Postava nemôže vstúpiť na políčko, ktoré patrí do územia s vyšším požadovaným levelom aký má.

## map_points
Obsahuje body, ktoré tvoria hernú plochu. Každý bod má svoje súradnice a patrí do nejakej oblasti.

## combat_log
Obsahuje záznam akcií postáv alebo postavy a moba v boji proti sebe - ich počet životov po vykonaní akcie, použitú schopnosť ak bola použitá a koľko postava poškodenia dostala alebo udelila.

## death_log
Obsahuje záznam smrtí postavy, vrátane toho, ktorá iná postava alebo mob ju zabila a na akom bode mapy.

## exp_log
Obsahuje záznam získaných exp bodov postavy. K získaniu týchto bodov sa môže viazať zabitie moba, iného hráča alebo dokončenie úlohy.

## levels
Samostatná tabuľka, ktorá obsahuje iba informáciu o tom, koľko exp bodov je nutné mať na dosiahnutie danej úrovne.