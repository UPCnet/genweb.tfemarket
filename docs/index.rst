=============================
MANUAL TFE (genweb.tfemarket)
=============================

1 - Sol·licitar un Mercat de TFE

2 - Configuració del Mercat

3 - Permisos y rols

3.1 - Gestor del TFE

3.2 - Professors

3.3 - Estudiants

4 - Continguts

4.1 - Mercat

4.1.1 - Camps

4.1.2 - Continguts que podem afegir

4.2 - Oferta

4.2.1 - Camps

4.2.2 - Continguts que podem afegir

4.2.3 - Limitacions

4.3 - Sol·licitud

4.3.1 - Camps

4.3.2 - Limitacions

1. Sol·licitar un Mercat de TFE
===============================

En qualsevol Genweb que tingui instal·lat el paquet "genweb.upc",
s’haurá d’instal·lar el paquet "genweb.tfemarket".

2. Configuració del Mercat
==========================

Abans de publicar el mercat i per tal de que sigui funcional, 'han
d'omplir els següent paràmetres. Des de l'opció "Mercat de TFE" de la
"Configuració", només visible per als Gestor del mercat:

**Configuració**

  **Codi del centre**
    Codi UPC del centre, aquest paràmetre s'utilitza
    per assignar els codis de les ofertes i per importa les titulacions
    del centre.

  **Nom del centre**
    Nom o sigles del centre.

  **Estat de revisió actiu**
    Si aquesta opció està seleccionada, les
    ofertes de treballs han de passar per un revisor, qualsevol gestor
    del mercat abans de ser publicades.

  **Tipus d'inscripció**
    "Inscripció" o "Registre" en funció del tractament que PRISMA hagi de
    fer amb les dades.

**Titulacions**

  Es poden omplir els camps de la taula manualment o utilitzar l’enllaç
  disponible per importar les titulacions corresponents al codi del
  centre a partir d’un fitxer en format "csv", que es descriu més
  endavant.

**Ofertes**

  **Mesos fins a la caducitat**
    Número de mesos fins que les ofertes caduquin
    automàticament desde la seva publicació. Si s'especifica una altra data
    de caducitat a l'oferta aquesta última serà la data vàlida.

  **Importar ofertes**
    Permet importa les ofertes de forma massiva des
    d'un fitxer amb format csv.

  **Nombre d'ofertes creades**
    comptador d'ofertes que s'incrementa de
    forma automàtica. Es pot reiniciar des del enllaç de la descripció.

**Classificacions**

-  Temàtiques principals dels TFE's: llista prefixada de temàtiques dels
   treballs.
-  Llistat de paraules clau: llista limitada de paraules clau que
   serveixen per cercar els treballs per matèries o interessos. S'ha
   d'afegir una per línea i sempre en minúscules.
-  Idiomes d'elaboració del treball: seleccionar el idiomes disponibles
   per a l'elaboració dels treballs. Si es necessite un altre s'ha de
   demanar via tiquet al ATIC per tal d'adaptar l'aplicació.

3. Permisos y rols
==================

Es recomana l'ús de grups d'accés per a la gestió del permisos del
mercat. Des de l'opció "Usuaris i grups" de la "Configuració del lloc"
s'assigna a cada grup el rol adient.

3.1. Gestor del TFE
-------------------

Persona que gestionarà el mercat i tindrà el rol de revisor. Si s'activa
l'opció de revisió, comprovarà que les ofertes són correctes abans de
publicar-les. Pot crear els mercats de TFE, les ofertes i camviar
l'estat del elements del mercat en cas d'error dels ususaris.

3.2. Professors
---------------

Afegir el grup o grups de professors que han de poder crear ofertes i
assignar-los el rol "TFE Teacher". Pot crear ofertes pròpies, gestionar
les sol·licituds de les seves ofertes i veure les ofertes públiques.

3.3. Estudiants
---------------

Afegir el grup o grup d'estudiants que han de poder sol·licitar les
ofertes i assignar-los el rol "TFE Student". Podran sol·licitar una
oferta i gestionar-la.

4. Continguts
=============

4.1. Mercat
-----------

El Mercat de treballs de fi d'estudis es un contingut del genweb que es
pot afegir a qualsvol lloc.

4.1.1. Camps
^^^^^^^^^^^^

**Títol**
  Camp de text.

**Descripció**
  Camp de text.

4.1.2. Continguts que podem afegir
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  Oferta

4.2. Oferta
-----------

Dintre d’un mercat els usuaris amb rol de professor poden afegir les
ofertes.

4.2.1. Camps
^^^^^^^^^^^^

**Títol**
  Camp de text.

**Descripció**
  Camp de text.

**Tema**
  Camp seleccionable que s’omple a partir de la configuració feta en
  l’apartat Temàtiques principals dels TFE's, només és pot seleccionar una
  opció.

**Grau**
  Camp seleccionable que s’omple a partir de la configuració feta en
  l’apartat Titulacions, podrem seleccionar més d’una opció.

**Paraules clau**
  Camp seleccionable que s’omple a partir de la
  configuració feta en l’apartat Llistat de paraules clau, podrem
  seleccionar més d’una opció.

**Direcció**
  Compost dels camps Professor, Nom del professor, Correu del
  professor i Departament. Aquest s’omplen automàticament amb la
  informació del professor que està creant l’oferta. En el cas de voler
  seleccionar un altre professor podem fer us del botó Cerca el professor,
  a partir del modal que sobre tindrem que afegir el nom d’usuari
  (nom.cognom) del professor que volem afegir i donar-l’hi a
  cercar. Finalment afegirem les dades del professor clican’t sobre el +.

**Nombre d'estudiants**
  Per defecte 1, amb un màxim possible de 10 estudiants.

**Càrrega de treball**
  Camp de text amb format.

**Objectius**
  Camp de text amb format.

**Característiques**
  Camp de text amb format.

**Requisits**
  Camp de text amb format.

**Idioma del treball**
  Camp seleccionable que s’omple a partir de la configuració feta en
  l’apartat Idiomes d’elaboració del treball, podrem seleccionar
  més d’una opció.

**Modalitat**
  Camp de selecció d’una opció entre Universitat i Empresa.

**Codirector**
  Camp de text.

**Empresa**
  Camp de text.

**Dades de contacte de l'empresa**
  Camp de text.

**Adreça de correu de l'empresa**
  Camp de text.

**Possibilitat de beca**
  Checkbox.

**Confidencial**
  Checkbox.

**Temàtica ambiental**
  Checkbox.

**Ambit de cooperació**
  Checkbox.

**Data de publicació**
  Per defecte el día següent a les 00:00.

**Data de venciment**
  Per defecte dintre de un any a les 23:59

4.2.2. Continguts que podem afegir
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

-  Fitxer (permisos mínims de professor)
-  Pàgina (permisos mínims de professor)
-  Sol·licitud (permisos de estudiant)

4.2.3. Limitacions
^^^^^^^^^^^^^^^^^^

Per poder eliminar una oferta aquesta no ha de tenir ninguna sol·licitud
activa.

4.3. Sol·licitud
----------------

Dintre d’una oferta els usuaris amb rol d'estudiant poden sol·licitar
aquelles ofertes que estiguin publicades, però només poden tenir una
sol·licitud activa. Per tal de crear una nova han de cancel·lar la que
tingui activa.

4.3.1. Camps
^^^^^^^^^^^^

Per defecte una sol·licitud al crear-la s’autocompleta amb les dades del
estudiant: Nom complet, DNI i Correu. L’estudiant tindrà accés a afegir
les següents dades.

**Telèfon**
  Camp de text.

**Comentaris**
  Camp de text amb format.

4.3.2. Limitacions
^^^^^^^^^^^^^^^^^^

Un usuari només pot tenir una sol·licitud activa. Per tornar a
sol·licitar una altre oferta caldrà cancel·lar aquesta o que el
professor se la denegi.
