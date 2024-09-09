"""data_mig_tcf_purpose_header_and_descript

Data migration to add new TCF purpose headers and update
existing TCF descriptions, provided they haven't been updated yet.

Revision ID: cc37edf20859
Revises: 1332815dcd71
Create Date: 2024-08-29 20:43:56.657171

"""

from datetime import datetime

from alembic import op
from loguru import logger
from sqlalchemy import text

from fides.api.alembic.migrations.helpers.database_functions import generate_record_id

# revision identifiers, used by Alembic.
revision = "cc37edf20859"
down_revision = "1332815dcd71"
branch_labels = None
depends_on = None

# fmt: off
updated_translations = {
    "lv": {
        "purpose_header": "Mēs kopā ar partneriem apstrādājam datus šādiem mērķiem",
        "description": "Mēs un mūsu __VENDOR_COUNT_LINK__ partneri izmantojam sīkfailus un citas saistītās tehnoloģijas, lai palīdzētu mums identificēt apmeklētājus un saglabāt viņu preferences. Šīs tehnoloģijas varam izmantot arī, lai mērķētu reklāmas, izmērītu reklāmas kampaņu panākumu līmeni un pārbaudītu vietnes trafiku. Lai gan dažas no šīm tehnoloģijām nav obligātas, tomēr tās palīdz uzlabot lietotāja pieredzi dažādos veidos, citas savukārt ir nepieciešamas, lai garantētu, ka pakalpojums vai vietne darbojas, atbilstošā veidā, un tās nedrīkst atspējot. \n\nLai apstrādātu personas datus, mēs kopā ar __VENDOR_COUNT_LINK__ partneriem saglabājam un/vai piekļūstam informācijai lietotāja ierīcē, piemēram, IP adresēm, unikālajiem identifikatoriem un sīkfailos saglabātajiem pārlūkošanas datiem. Izvēloties opciju \"Pārvaldīt iestatījumus\", kas atrodama lapas kājenē, varat kontrolēt savus iestatījumus. Lūdzu, apmeklējiet mūsu pārdevēju/ pakalpojumu sniedzēju lapu, lai pārbaudītu vai iebilstu pret jebkādiem gadījumiem, kad mūsu partneri apgalvo, ka viņiem ir leģitīmais pamats izmantot jūsu datus."
    },
    "et": {
        "purpose_header": "Meie ja meie partnerid töötleme andmeid järgmistel eesmärkidel",
        "description": "Meie ja meie __VENDOR_COUNT_LINK__ partnerid kasutame küpsiseid ja sarnaseid meetodeid külastajate äratundmiseks ja nende eelistuste meelespidamiseks. Võime neid tehnoloogiaid kasutada ka reklaamikampaaniate tõhususe hindamiseks, reklaami suunamiseks ja veebisaidi külastatavuse analüüsimiseks. Mõned neist tehnoloogiatest on teenuse või veebisaidi nõuetekohase toimimise tagamiseks hädavajalikud ja neid ei saa keelata, teised on vabatahtlikud, kuid parandavad eri viisidel kasutajakogemust. \n\nKoostöös oma __VENDOR_COUNT_LINK__ partneritega salvestame ja/või kasutame kasutaja seadmes olevat teavet, sealhulgas, kuid mitte ainult, IP-aadresse, unikaalseid identifikaatoreid ja küpsistesse salvestatud sirvimisandmeid, et töödelda isikuandmeid. Teil on võimalus oma eelistusi hallata, valides lehekülje jaluses oleva valiku „Eelistuste haldamine“. Kui soovite vaadata juhtumeid, kus meie partnerid väidavad, et neil on õigustatud huvi teie andmete kasutamiseks, või neile juhtumitele vastuväiteid esitada, külastage palun meie kaupmeeste lehekülge."
    },
    "el": {
        "purpose_header": "Εμείς και οι συνεργάτες μας επεξεργαζόμαστε δεδομένα για τους ακόλουθους σκοπούς",
        "description": "Εμείς και οι συνεργάτες μας __VENDOR_COUNT_LINK__ χρησιμοποιούμε cookie και παρόμοιες μεθόδους για να αναγνωρίζουμε τους επισκέπτες και να θυμόμαστε τις προτιμήσεις τους. Ενδέχεται επίσης να χρησιμοποιήσουμε αυτές τις τεχνολογίες για να μετρήσουμε την αποτελεσματικότητα των διαφημιστικών εκστρατειών, να στοχεύσουμε διαφημίσεις και να αναλύσουμε την επισκεψιμότητα του ιστότοπου. Ορισμένες από αυτές τις τεχνολογίες είναι απαραίτητες για τη διασφάλιση της σωστής λειτουργίας της υπηρεσίας ή του ιστότοπου και δεν μπορούν να απενεργοποιηθούν, ενώ άλλες είναι προαιρετικές, αλλά χρησιμεύουν για τη βελτίωση της εμπειρίας του χρήστη με διάφορους τρόπους. \n\nΕμείς, σε συνεργασία με τους συνεργάτες μας __VENDOR_COUNT_LINK__, αποθηκεύουμε ή/και έχουμε πρόσβαση σε πληροφορίες στη συσκευή ενός χρήστη, συμπεριλαμβανομένων, ενδεικτικά, διευθύνσεων IP, μοναδικών αναγνωριστικών και δεδομένων περιήγησης που είναι αποθηκευμένα σε cookie, προκειμένου να επεξεργαστούμε προσωπικά δεδομένα. Έχετε την επιλογή να διαχειριστείτε τις προτιμήσεις σας επιλέγοντας την επιλογή «Διαχείριση προτιμήσεων» που βρίσκεται στο υποσέλιδο. Για να επιθεωρήσετε ή να εναντιωθείτε σε περιπτώσεις όπου οι συνεργάτες μας ισχυρίζονται ότι έχουν έννομο συμφέρον να χρησιμοποιήσουν τα δεδομένα σας, επισκεφτείτε τη σελίδα των προμηθευτών μας."
    },
    "it": {
        "purpose_header": "Noi e i nostri partner elaboriamo i dati per le finalità seguenti",
        "description": "Noi e i nostri __VENDOR_COUNT_LINK__ partner utilizziamo cookie e metodi analoghi per riconoscere i visitatori e ricordare le loro preferenze. Possiamo anche utilizzare queste tecnologie per verificare l’efficacia di campagne pubblicitarie, inviare pubblicità mirate, ed analizzare il traffico verso il sito. Alcune di queste tecnologie sono essenziali per assicurare il funzionamento del servizio o del sito e non possono essere disabilitate; altre sono opzionali ma migliorano l’esperienza degli utilizzatori in vari modi. \n\nInsieme ai nostri __VENDOR_COUNT_LINK__ partner, registriamo e/o leggiamo informazioni sul dispositivo dell’utente, compresi ma non limitate a: indirizzi IP, identificativi unici, e dati di navigazione conservati nei cookie, al fine di gestire i dati personali. Hai la possibilità di gestire le tue preferenze selezionando l'opzione \"Gestisci preferenze\" in fondo alla pagina. Per verificare o opporsi in quei casi in cui i nostri partner dichiarano un interesse legittimo nell'utilizzo dei tuoi dati, visita la nostra pagina sui fornitori."
    },
    "es": {
        "purpose_header": "Nosotros y nuestros socios tratamos datos para los siguientes fines",
        "description": "Nosotros y nuestros __VENDOR_COUNT_LINK__ socios utilizamos cookies y métodos similares para reconocer a los visitantes y recordar sus preferencias. También podemos utilizar estas tecnologías para medir la eficacia de las campañas publicitarias, orientar los anuncios de forma selectiva y analizar el tráfico del sitio web. Algunas de estas tecnologías son esenciales para garantizar el funcionamiento correcto del servicio o del sitio web y no se pueden desactivar, mientras que otras son opcionales pero sirven para mejorar la experiencia del usuario de diversas maneras. \n\nNosotros, en colaboración con nuestros __VENDOR_COUNT_LINK__ socios, almacenamos y/o accedemos a información en el dispositivo de un usuario, p. ej. direcciones IP, identificadores únicos y datos de navegación almacenados en cookies, con el fin de tratar datos personales. Tiene la opción de administrar sus preferencias seleccionando la opción «Administrar preferencias» que figura en el pie de página. Para revisar u oponerse a los casos en los que nuestros socios afirman tener un interés legítimo en utilizar sus datos, visite nuestra página de proveedores."
    },
    "ja": {
        "purpose_header": "当社およびパートナーは、以下の目的でデータを処理します。",
        "description": "当社および__VENDOR_COUNT_LINK__パートナーは、訪問者を認識し、その設定を記憶するためにクッキーや同様の方法を使用します。また、当社は、広告キャンペーンの効果を測定し、広告対象を絞り込み、ウェブサイトのトラフィックを分析するためにこれらの技術を使用します。これらの技術の一部は、サービスまたはウェブサイトが正しく機能するために必須であり、無効にすることができません。その他は選択可能ですが、様々な形でユーザー体験の向上に役立ちます。 \n\n当社は、__VENDOR_COUNT_LINK__パートナーと協力し、ユーザーのデバイスに情報を保存し、またそれらの情報にアクセスします。これらの情報には、個人データを処理するためクッキーに保存されるIPアドレス、一意識別子、閲覧データなどが含まれます。本ページ下部にある［Manage Preferences］オプションを選択すると、設定を変更できます。当社のパートナーが個人データ利用の正当な利益を主張する事例を検証するには、またはこれに異議を申し立てるには、当社のベンダーのページにアクセスしてください。"
    },
    "bs": {
        "purpose_header": "Mi i naši partneri obrađujemo podatke u sljedeće svrhe",
        "description": "Mi i naši __VENDOR_COUNT_LINK__ partneri koristimo kolačiće i slične metode kako bismo prepoznali posjetitelje i zapamtili njihove preferencije. Ove tehnologije možemo koristiti i za mjerenje učinkovitosti oglasnih kampanja, ciljanje oglasa i analizu saobraćaja na web lokaciji. Neke od ovih tehnologija bitne su za osiguravanje ispravnog rada usluge ili web stranice i ne mogu se onemogućiti, dok su druge opcionalne, ali služe za poboljšanje korisničkog iskustva na različite načine. \n\nMi, u suradnji s našim __VENDOR_COUNT_LINK__ partnerima, informacije pohranjujemo i/ili im pristupamo na korisnikovom uređaju, uključujući, ali ne ograničavajući se na IP adrese, jedinstvene identifikatore i podatke o pregledavanju pohranjene u kolačićima, u cilju obrade ličnih podataka. Imate mogućnost da upravljate svojim postavkama odabirom opcije 'Upravljanje postavkama' koja se nalazi u podnožju stranice. Posjetite stranicu naših dobavljača kako biste pregledali ili uložili prigovor na slučajeve u kojima naši partneri tvrde da imaju legitiman interes za korištenje vaših podataka."
    },
    "zh": {
        "purpose_header": "我们和我们的合作伙伴处理数据的目的如下",
        "description": "我们和 __VENDOR_COUNT_LINK__ 合作伙伴使用 cookie 和类似方法来识别访客并记住他们的偏好。我们还可能使用这些技术来衡量广告活动的有效性，定位广告并分析网站流量。其中一些技术对于确保服务或网站的正常运行至关重要，并且不能被禁用。其他技术则是可选的，但它们可以通过各种方式增强用户体验。 \n\n我们与 __VENDOR_COUNT_LINK__ 合作伙伴合作，在用户设备上存储和/或访问信息，包括但不限于 IP 地址、唯一标识符以及存储在 Cookie 中的浏览数据，以便处理个人数据。您可以通过选择页面页脚中的“管理首选项”选项来管理您的首选项。要查看或反对我们的合作伙伴主张使用您数据的合法权益情况，请访问我们的供应商页面。"
    },
    "bg": {
        "purpose_header": "Ние и нашите партньори обработваме данни за следните цели",
        "description": "Ние и нашите __VENDOR_COUNT_LINK__ партньори използваме „бисквитки“ и подобни методи, за да разпознаваме посетителите и да запомняме техните предпочитания. Възможно е също така да използваме тези технологии, за да измерваме ефективността на рекламните кампании, да насочваме реклами и да анализираме трафика на уебсайта. Някои от тези технологии са от съществено значение за осигуряване на правилното функциониране на услугата или уебсайта и не могат да бъдат деактивирани, докато други не са задължителни, но служат за подобряване на потребителското изживяване по различни начини. \n\nЗа да обработваме лични данни ние, в сътрудничество с нашите __VENDOR_COUNT_LINK__ партньори, съхраняваме и/или получаваме достъп до информация на устройството на потребителя, включително, но не само, IP адреси, уникални идентификатори и данни за сърфиране, съхранявани в бисквитки. Имате възможност да управлявате предпочитанията си, като изберете опцията „Управление на предпочитанията“, която се намира в долния колонтитул на страницата. За да прегледате или възразите срещу случаите, в които нашите партньори заявяват законен интерес да използват Вашите данни, моля, посетете страницата ни за доставчици."
    },
    "ar": {
        "purpose_header": "نقوم نحن وشركاؤنا بمعالجة البيانات للأغراض التالية",
        "description": "نحن وشركاؤنا __VENDOR_COUNT_LINK__ نستخدم ملفات تعريف الارتباط وطرقًا مماثلة للتعرف على الزوار وتذكر تفضيلاتهم. قد نستخدم أيضًا هذه التقنيات لقياس فعالية الحملات الإعلانية، واستهداف الإعلانات وتحليل حركة مرور الموقع الإلكتروني. بعض هذه التقنيات ضرورية ولا يمكن تعطيلها لضمان سير الخدمة أو الموقع الإلكتروني، وقد يكون بعضها الآخر اختياري وتعمل على تحسين تجربة المستخدم بطرق مختلفة. \n\nبالتعاون مع شركائنا __VENDOR_COUNT_LINK__، نخزّن و/أو نتيح الوصول إلى المعلومات الموجودة على جهاز المستخدم بما في ذلك على سبيل المثال لا الحصر: عناوين الآي بي، ومعرفات فريدة، وبيانات تصفح مخزنة في ملفات تعريف الارتباط، لمعالجة البيانات الشخصية. لديك خيار إدارة تفضيلاتك عن طريق تحديد خيار \"إدارة التفضيلات\" الموجود في أسفل الصفحة. للمراجعة أو الاعتراض على الحالات التي يؤكد فيها شركاؤنا على مصلحة مشروعة في استخدام بياناتك، يرجى زيارة صفحة البائعين لدينا."
    },
    "tr": {
        "purpose_header": "Biz ve ortaklarımız aşağıdaki amaçlarla verileri işleriz",
        "description": "Biz ve __VENDOR_COUNT_LINK__ ortaklarımız, ziyaretçileri tanımak ve tercihlerini hatırlamak için çerezleri ve benzer yöntemleri kullanırız. Bu teknolojileri ayrıca reklam kampanyalarının etkinliğini ölçmek, reklamları hedefe yönelik olarak göstermek ve web sitesi trafiğini analiz etmek için de kullanabiliriz. Bu teknolojilerden bazıları, hizmetin veya web sitesinin düzgün çalışmasını sağlamak için gereklidir ve devre dışı bırakılamaz; diğerleri ise isteğe bağlıdır ancak kullanıcı deneyimini çeşitli şekillerde geliştirmeye yarar. \n\n__VENDOR_COUNT_LINK__ ortaklarımızla iş birliği içinde, kişisel verileri işlemek için IP adresleri, benzersiz tanımlayıcılar ve çerezlerde depolanan tarama verileri dahil ancak bunlarla sınırlı olmamak üzere bir kullanıcının cihazındaki bilgileri depolar ve/veya bunlara erişiriz. Sayfanın alt kısmında bulunan “Tercihleri Yönet” seçeneğini belirleyerek tercihlerinizi yönetebilirsiniz. Ortaklarımızın verilerinizi kullanma konusunda meşru menfaat öne sürdüğü durumları incelemek veya bunlara itiraz etmek için lütfen satıcılar sayfamızı ziyaret edin."
    },
    "hu": {
        "purpose_header": "Partnereinkkel együttműködve a következő célokból kezelünk adatokat",
        "description": "__VENDOR_COUNT_LINK__ partnerünkkel együttműködve sütiket és hasonló módszereket használunk a látogatók felismerésére és beállításaik megjegyzésére. Ezeket a technológiákat a reklámkampányok hatékonyságának mérésére, a hirdetések célzására és a weboldal forgalmának elemzésére is használhatjuk. Ezen technológiák némelyike elengedhetetlen a szolgáltatás vagy a weboldal megfelelő működéséhez, és nem kapcsolható ki, míg mások opcionálisak, de különböző módon szolgálják a felhasználói élmény fokozását. \n\n__VENDOR_COUNT_LINK__ partnerünkkel együttműködve a személyes adatok feldolgozása érdekében információkat érünk el és/vagy tárolunk a felhasználó eszközén, beleértve, de nem kizárólagosan az IP-címeket, egyedi azonosítókat és a sütikben tárolt böngészési adatokat. Lehetősége van a beállítások kezelésére az oldal láblécében található „Beállítások kezelése” opció kiválasztásával. Az olyan esetek áttekintéséhez vagy kifogásolásához, amikor partnereink jogos érdeke fűződik az Ön adatainak felhasználásához, kérjük, látogasson el szállítói oldalunkra."
    },
    "pt-PT": {
        "purpose_header": "Nós e os nossos parceiros tratamos dados para as seguintes finalidades",
        "description": "Nós e os nossos parceiros __VENDOR_COUNT_LINK__utilizamos cookies e métodos semelhantes para reconhecer os visitantes e recordar as suas preferências. Também podemos utilizar estas tecnologias para avaliar a eficácia das campanhas publicitárias, direcionar anúncios e analisar o tráfego do website. Algumas destas tecnologias são essenciais para garantir o bom funcionamento do serviço ou do Web site e não podem ser desativadas, enquanto outras são opcionais, mas servem para melhorar a experiência do utilizador de várias formas. \n\nEm colaboração com os nossos parceiros __VENDOR_COUNT_LINK__, armazenamos e/ou acedemos a informações no dispositivo de um utilizador, incluindo, entre outros, endereços IP, identificadores únicos e dados de navegação armazenados em cookies, a fim de processar dados pessoais. Tem a opção de gerir as suas preferências selecionando a opção \"Gerir Preferências\" localizada no rodapé da página. Para rever ou opor-se a situações em que os nossos parceiros afirmam ter um interesse legítimo na utilização dos seus dados, visite a nossa página de fornecedores."
    },
    "sv": {
        "purpose_header": "Vi och våra partners behandlar uppgifter i följande syften",
        "description": "Vi och våra __VENDOR_COUNT_LINK__ partners använder kakor och liknande metoder för att känna igen besökare och komma ihåg deras inställningar. Vi kan också komma att använda dessa funktioner för att mäta effektiviteten av marknadsföringskampanjer, riktad marknadsföring och analysera webbplatsens trafik. Vissa av dessa funktioner är nödvändiga för att försäkra att webbplatsens tjänster fungerar som de ska och kan inte avaktiveras, medan andra är valfria men är till för att förbättra användarupplevelsen på olika sätt. \n\nVi, i samarbete med våra __VENDOR_COUNT_LINK__ partners, lagrar och/eller har tillgång till information på en användares enhet, inbegripet men inte begränsat till IP-adresser, unika identifieringskoder, och webbinformationen lagrad i kakor för att behandla personuppgifter. Du har möjligheten att hantera dina inställningar i menyn ”Hantera inställningar” längst ner på sidan. För att granska eller avböja instanser där våra partners hävdar berättigat intresse i användningen av din data, se våra leverantörers sidor."
    },
    "uk": {
        "purpose_header": "Ми та наші партнери обробляємо дані для вказаних нижче цілей",
        "description": "Ми та наші партнери __VENDOR_COUNT_LINK__ використовуємо файли cookie та подібні методи для розпізнавання відвідувачів і запам’ятовування їхніх вподобань. Ми також можемо використовувати ці технології для оцінки ефективності рекламних кампаній, таргетування реклами та аналізу відвідуваності вебсайтів. Деякі з цих технологій необхідні для забезпечення належного функціонування сервісу або вебсайту і не можуть бути відключені, тоді як інші є необов’язковими, проте різними способами слугують для покращення користувацького досвіду. \n\nУ співпраці з нашими партнерами __VENDOR_COUNT_LINK__ ми зберігаємо і/або отримуємо доступ до інформації на пристрої користувача, включаючи, зокрема, IP-адреси, унікальні ідентифікатори та дані перегляду, що зберігаються в файлах cookie, з метою обробки персональних даних. Ви можете керувати своїми налаштуваннями, вибравши опцію «Керувати налаштуваннями», розташовану в нижньому колонтитулі сторінки. Щоб переглянути або заперечити проти випадків, коли наші партнери заявляють про законний інтерес у використанні ваших даних, завітайте на сторінку наших постачальників."
    },
    "sr-Latn": {
        "purpose_header": "Mi i naši partneri obrađujemo podatke u sledeće svrhe",
        "description": "Mi i naši __VENDOR_COUNT_LINK__ partneri koristimo kolačiće i slične metode da bismo prepoznali posetioce i zapamtili njihove postavke. Ove tehnologije možemo da koristimo i za procenu efikasnosti reklamnih kampanja, ciljanje oglasa i analizu saobraćaja na veb-lokacijama. Neke od ovih tehnologija su od suštinskog značaja za obezbeđivanje pravilnog funkcionisanja usluge ili veb-lokacije i ne mogu se onemogućiti, dok su druge opcione, a služe za poboljšanje korisničkog iskustva na različite načine. \n\nU saradnji sa našim __VENDOR_COUNT_LINK__ partnerima, mi čuvamo informacije i/ili im pristupamo na korisnikovom uređaju, uključujući, između ostalog, IP adrese, jedinstvene identifikatore i podatke o pregledanju uskladištene u kolačićima u cilju obrade ličnih podataka. Imate mogućnost da upravljate svojim željenim postavkama tako što ćete izabrati opciju „Upravljanje podešavanjima“ koja se nalazi u podnožju stranice. Da biste pregledali ili uložili prigovor na slučajeve u kojima naši partneri tvrde da imaju legitiman interes za korišćenje vaših podataka, posetite našu stranicu dobavljača."
    },
    "sk": {
        "purpose_header": "My a naši partneri spracúvame údaje na tieto účely",
        "description": "My a naši __VENDOR_COUNT_LINK__ partneri používame súbory cookie a podobné metódy na rozpoznanie návštevníkov a zapamätanie ich predvolieb. Tieto technológie môžeme používať aj na meranie účinnosti reklamných kampaní, cielenie reklamy a analýzu návštevnosti webových stránok. Niektoré z týchto technológií sú nevyhnutné na zabezpečenie správneho fungovania služby alebo webových stránok a nemožno ich vypnúť, zatiaľ čo iné sú voliteľné, ale slúžia na zlepšenie používania rôznymi spôsobmi. \n\nV spolupráci s našimi __VENDOR_COUNT_LINK__ partnermi ukladáme a/alebo pristupujeme k informáciám v zariadení používateľa, okrem iného k adresám IP, jedinečným identifikátorom a údajom o prehliadaní uloženým v súboroch cookie, aby sme mohli spracúvať osobné údaje. Svoje predvoľby môžete spravovať výberom možnosti „Správa predvolieb“, ktorá sa nachádza v dolnej časti stránky. Ak chcete skontrolovať alebo namietať proti prípadom, keď naši partneri uplatňujú oprávnený záujem pri využívaní vašich údajov, navštívte stránku našich dodávateľov."
    },
    "ro": {
        "purpose_header": "Noi și partenerii noștri prelucrăm datele în următoarele scopuri",
        "description": "Noi și partenerii noștri __VENDOR_COUNT_LINK__ folosim module cookie și metode similare de recunoaștere a vizitatorilor și a reține preferințele lor. De asemenea, folosim aceste tehnologii pentru a cuantifica eficacitatea campaniilor de promovare, reclamele țintite și a analiza traficul de pe site-ul web. O parte dintre aceste tehnologii sunt esențiale pentru a garanta funcționarea corespunzătoare a serviciului sau a site-ului web și nu pot fi dezactivate, în timp ce altele sunt opționale, dar servesc la îmbunătățiraea experienței utilizatorului în diverse moduri. \n\nNoi, în colaborare cu partenerii noștri __VENDOR_COUNT_LINK__ , stocăm și/sau accesăm informațiile de pe un dispozitiv al utilizatorului, inclusiv, dar fără a se limita la adresele IP, identificatorii unici și explorarea datelor stocate în modulele cookie, pentru a prelucra datele dvs. cu caracter personal. Aveți opțiunea de a vă gestiona preferințele selectând opțiunea „Gestionare preferințe” situată în subsolul paginii. Pentru a revizui sau a vă opune instanțelor în care partenerii noștri declară un interes legitim vis-a-vis de utilizarea datelor dvs., vizitați pagina noastră de furnizori."
    },
    "pl": {
        "purpose_header": "My i nasi partnerzy przetwarzamy dane w niżej wymienionych celach",
        "description": "My i nasi partnerzy __VENDOR_COUNT_LINK__ wykorzystujemy pliki cookie i podobne metody do rozpoznawania odwiedzających i zapamiętywania ich preferencji. Możemy także wykorzystywać te technologie do mierzenia skuteczności kampanii reklamowych i reklam celowanych oraz analizowania ruchu w witrynie. Niektóre z tych technologii są konieczne do zapewnienia prawidłowego działania usługi lub witryny i nie mogą być dezaktywowane, a inne są opcjonalne ale służą do zapewnienia większego komfortu użytkownikowi na różne sposoby. \n\nWe współpracy z naszymi partnerami __VENDOR_COUNT_LINK__ przechowujemy informacje – w tym między innymi adresy IP, niepowtarzalne identyfikatory i dane z przeglądania stron zapisane w plikach cookie – i/ub uzyskujemy do nich dostęp na urządzeniu użytkownika, aby przetwarzać dane osobowe. Mają Państwo możliwość zarządzania swoimi preferencjami przez wybranie opcji „Zarządzaj preferencjami” dostępnej w stopce strony. W celu weryfikacji przypadków, w których nasi partnerzy domagają się uznania uzasadnionego interesu w wykorzystywaniu Państwa danych, lub sprzeciwienia się nim, można odwiedzić naszą stronę dla dostawców."
    },
    "lt": {
        "purpose_header": "Mes ir mūsų partneriai tvarkome duomenis šiais tikslais",
        "description": "Mes ir mūsų __VENDOR_COUNT_LINK__ partneriai naudojame slapukus ir panašius metodus, kad atpažintume lankytojus ir įsimintume jų nuostatas. Šias technologijas taip pat galime naudoti siekdami įvertinti reklamos kampanijų veiksmingumą, nukreipti reklamą ir analizuoti svetainės lankomumą. Kai kurios iš šių technologijų yra būtinos tinkamam paslaugos ar svetainės veikimui užtikrinti ir negali būti išjungtos, o kitos yra neprivalomos, tačiau padeda įvairiais būdais pagerinti naudotojo patirtį. \n\nMes, bendradarbiaudami su __VENDOR_COUNT_LINK__ partneriais, saugome ir (arba) prieiname prie naudotojo įrenginyje esančios informacijos, įskaitant, bet neapsiribojant, IP adresus, unikalius identifikatorius ir naršymo duomenis, saugomus slapukuose, kad galėtume tvarkyti asmens duomenis. Savo nuostatas galite tvarkyti pasirinkę puslapio poraštėje esančią parinktį „Tvarkyti nuostatas“. Jei norite peržiūrėti arba nesutikti su atvejais, kai mūsų partneriai nurodo teisėtą interesą naudoti jūsų duomenis, apsilankykite mūsų pardavėjų puslapyje."
    },
    "hr": {
        "purpose_header": "Mi i naši partneri obrađujemo podatke za sljedeće svrhe",
        "description": "Mi i naši __VENDOR_COUNT_LINK__ partneri koristimo kolačiće i slične metode kako bismo prepoznali posjetitelje i zapamtili njihove sklonosti. Ove tehnologije također možemo koristiti za procjenu učinkovitosti reklamnih kampanja, ciljanih oglasa i analizu prometa web-mjesta. Neke od ovih tehnologija ključne su za osiguravanje pravilnog funkcioniranja usluge ili web-mjesta i ne mogu biti onesposobljene, dok druge nisu obavezne, ali služe za poboljšanje korisničkog doživljaja na različite načine. \n\nMi, u suradnji s našim __VENDOR_COUNT_LINK__ partnerima, pohranjujemo i/ili pristupamo informacijama na korisnikovom uređaju, uključujući, ali ne ograničavajući se na IP adrese, jedinstvene identifikatore i pregledavanje podataka pohranjenih u kolačićima kako bismo obradili osobne podatke. Vi imate mogućnost upravljanja preferencijama odabirom opcije „Upravljanje preferencijama“ koja se nalazi u podnožju stranice. Da biste pregledali ili prigovorili na slučajeve kada naši partneri tvrde da imaju legitimni interes za korištenje vaših podataka, posjetite našu stranicu za pružatelje usluga."
    },
    "no": {
        "purpose_header": "Vi og partnerne våre håndterer data for følgende hensikter",
        "description": "Vi og __VENDOR_COUNT_LINK__ partnerne våre bruker informasjonskapsler og lignende metoder til å kjenne igjen besøkende og huske preferansene deres. Det kan hende at vi også bruker disse teknologiene til å måle effektiviteten til annonsekampanjer, målrette annonser og analysere nettstedtrafikk. Enkelte av disse teknologiene er nødvendige for å sikre at tjenesten eller nettstedet fungerer som de skal, og de kan derfor ikke slås av. Andre er valgfrie, men funksjonen deres er å forbedre brukeropplevelsen på ulike måter. \n\nVi, i samarbeid med __VENDOR_COUNT_LINK__ partnerne våre, lagrer og/eller får tilgang til informasjon på en brukers enhet. Dette inkluderer, men er ikke begrenset til, IP-adresser, unike identifikatorer og nettleserdata lagret i informasjonskapsler, sånn at disse kan behandle personlige data. Du har muligheten til å administrere preferansene dine ved å velge alternativet «Administrer preferanser» nederst på siden. Hvis du vil kontrollere eller rette en innsigelse i tilfeller hvor partnerne våre hevder en legitim interesse i å bruke dataene dine, finner du mer info om dette på leverandørsiden vår."
    },
    "da": {
        "purpose_header": "Vi og vores partnere behandler data til følgende formål",
        "description": "Vi og vores __VENDOR_COUNT_LINK__ partnere bruger cookies og lignende metoder til at genkende besøgende og huske deres præferencer. Vi kan også bruge disse teknologier til at måle reklamekampagners effektivitet, målrette reklamer og analysere webstedstrafik. Nogle af disse teknologier er afgørende for at sikre, at tjenesten eller webstedet fungerer korrekt, og at den/det ikke kan deaktiveres, mens andre er valgfrie, men har til formål at forbedre brugeroplevelsen på forskellige måder. \n\nVi, i samarbejde med vores __VENDOR_COUNT_LINK__ partnere, gemmer og/eller tager os adgang til oplysninger på en brugers enhed, herunder, men ikke begrænset til IP-adresser, entydige id'er og browsingdata, der gemmes i cookies, for at behandle persondata. Du har mulighed for at administrere dine præferencer ved at vælge muligheden \"Administrer præferencer\", der er at finde i sidens sidefod. For at gennemgå eller komme med indsigelser til tilfælde, hvor vores partnere hævder at have en legitim interesse i anvendelsen af dine data kan du besøge siden Vores forhandlere."
    },
    "ca": {
        "purpose_header": "Nosaltres i els nostres socis tractem les dades amb les finalitats següents",
        "description": "Nosaltres i els nostres socis de __VENDOR_COUNT_LINK__ utilitzem galetes i mètodes semblants per reconèixer els visitants i recordar-ne les preferències. També podem utilitzar aquestes tecnologies per avaluar l’efectivitat de les campanyes publicitàries, dirigir els anuncis i analitzar el trànsit del lloc web. Algunes d’aquestes tecnologies són essencials per garantir el bon funcionament del servei o lloc web i no es poden desactivar, mentre que d’altres són opcionals però serveixen per millorar l’experiència de l’usuari de diverses maneres. \n\nNosaltres, en col·laboració amb els nostres socis de __VENDOR_COUNT_LINK__, accedim a informació del dispositiu d’un usuari o l’emmagatzemem. Aquesta informació inclou, entre d’altres, adreces IP, identificadors únics i dades de navegació emmagatzemades a les galetes per processar les dades personals. Podeu gestionar les vostres preferències seleccionant l’opció “Gestiona les preferències” que hi ha al peu de la pàgina. Si voleu revisar o oposar-vos als casos en què els nostres socis afirmen tenir un interès legítim per utilitzar les vostres dades, visiteu la nostra pàgina de proveïdors."
    },
    "de": {
        "purpose_header": "Wir und unsere Partner verarbeiten Daten für folgende Zwecke",
        "description": "Wir und unsere __VENDOR_COUNT_LINK__ Partner verwenden Cookies und ähnliche Techniken, um Besucher wiederzuerkennen und ihre Einstellungen zu speichern. Wir können diese Technologien auch verwenden, um die Effektivität von Werbekampagnen zu messen, Werbung gezielt zu platzieren und den Traffic der Website zu analysieren. Einige dieser Technologien sind für die ordnungsgemäße Funktion des Dienstes oder der Website unerlässlich und können nicht deaktiviert werden. Andere sind optional, dienen aber dazu, die Benutzererfahrung auf verschiedene Weise zu verbessern. \n\nIn Zusammenarbeit mit unseren __VENDOR_COUNT_LINK__ Partnern speichern wir Informationen auf den Geräten der Benutzer und/oder greifen darauf zu. Zu diesen Informationen zählen unter anderem IP-Adressen, eindeutige Kennungen und in Cookies gespeicherte Browserdaten, um persönliche Daten zu verarbeiten. Sie können Ihre Einstellungen verwalten, indem Sie in der Fußzeile der Seite auf die Option „Einstellungen verwalten“ klicken. Gehen Sie bitte auf unsere Seite für Anbieter, um Fälle zu prüfen, in denen unsere Partner ein berechtigtes Interesse an der Nutzung Ihrer Daten geltend machen, oder um der Nutzung zu widersprechen."
    },
    "pt-BR": {
        "purpose_header": "Nós e nossos parceiros processamos dados para os seguintes fins",
        "description": "Nós e nossos __VENDOR_COUNT_LINK__ parceiros usamos cookies e métodos semelhantes para reconhecer visitantes e lembrar suas preferências. Também podemos usar essas tecnologias para avaliar a eficácia de campanhas publicitárias, direcionar anúncios e analisar o tráfego do site. Algumas destas tecnologias são essenciais para garantir o bom funcionamento do serviço ou do site e não podem ser desativadas, enquanto outras são opcionais, mas servem para melhorar a experiência do usuário de diversas formas. \n\nNós, em colaboração com nossos __VENDOR_COUNT_LINK__ parceiros, armazenamos e/ou acessamos informações no dispositivo de um usuário, incluindo, mas não se limitando a, endereços de IP, identificadores únicos e dados de navegação armazenados em cookies, com o objetivo de processar dados pessoais. Você tem a opção de gerenciar suas preferências selecionando a opção “Gerenciar Preferências” localizada no rodapé da página. Para analisar ou contestar casos em que nossos parceiros aleguem ter um interesse legítimo na utilização de seus dados, visite nossa página de fornecedores."
    },
    "fr": {
        "purpose_header": "Nos partenaires et nous-mêmes traitons les données aux fins suivantes",
        "description": "Nos __VENDOR_COUNT_LINK__ partenaires et nous-mêmes utilisons des cookies et des méthodes similaires pour reconnaître les visiteurs de ce site et nous souvenir de leurs préférences. Nous pouvons également utiliser ces technologies pour mesurer l’efficacité des campagnes publicitaires et des publicités ciblées, et pour analyser le trafic sur le site Web. Certaines de ces technologies sont indispensables au bon fonctionnement du service ou du site Web et ne peuvent pas être désactivées, tandis que d’autres sont facultatives, mais permettent d’améliorer l’expérience de l’utilisateur de multiples façons. \n\nEn collaboration avec nos __VENDOR_COUNT_LINK__ partenaires, nous stockons ou consultons des informations sur l’appareil d’un utilisateur, y compris, mais sans s’y limiter, les adresses IP, les identifiants uniques et les données de navigation stockées par les cookies, afin de traiter les renseignements personnels. Vous avez la possibilité de gérer vos préférences en sélectionnant l’option « Gérer les préférences » située en pied de page. Pour consulter ou refuser les instances pour lesquelles nos partenaires invoquent un intérêt légitime d’utilisation de vos données, veuillez vous reporter à la page de nos fournisseurs."
    },
    "gl": {
        "purpose_header": "Os nosos socios e nós procesamos datos para os seguintes fins",
        "description": "Os nosos __VENDOR_COUNT_LINK__ socios e nós utilizamos cookies e métodos similares para recoñecer os visitantes e recordar as súas preferencias. Tamén podemos usar estas tecnoloxías para avaliar a efectividade das campañas publicitarias, dirixir anuncios e analizar o tráfico da web. Algunhas son esenciais para garantir un bo funcionamento do servizo ou da páxina web e non poden desactivarse, mentres que outras son opcionais pero serven para mellorar a experiencia do usuario de diversas maneiras. \n\nNós, en  colaboración cos nosos __VENDOR_COUNT_LINK__ socios, almacenamos e/ou accedemos á información dos dispositivos do usuario como direccións IP, identificadores únicos e datos de navegación gardados nas cookies para procesar a información persoal. Vostede ten a posibilidade de xestionar as súas preferencias seleccionando a opción \"Xestionar preferencias\" que se atopa ao pé da páxina. Para revisar ou oporse aos casos nos que os nosos socios afirman ter un interese lexítimo para utilizar os seus datos, visite a páxina dos nosos subministradores."
    },
    "cs": {
        "purpose_header": "My a naši partneři zpracováváme data pro následující účely",
        "description": "My a naši __VENDOR_COUNT_LINK__ partneři užíváme soubory cookie a podobné metody k rozpoznání návštěvníků a zapamatování jejich preferencí. Tyto technologie můžeme také použít k měření účinnosti reklamních kampaní, cílení reklam a analýze návštěvnosti webových stránek. Některé z těchto technologií jsou nezbytné pro zajištění správného fungování služby nebo webových stránek a nelze je deaktivovat, zatímco jiné jsou volitelné, ale slouží různými způsoby k vylepšení uživatelského zážitku. \n\nVe spolupráci s našimi __VENDOR_COUNT_LINK__ partnery ukládáme a/nebo přistupujeme k informacím na zařízení uživatele, včetně IP adres, jedinečných identifikátorů a údajů o prohlížení uložených v souborech cookie, za účelem zpracování osobních údajů. Máte možnost spravovat své předvolby výběrem možnosti „Spravovat předvolby“ v zápatí stránky. Chcete-li zkontrolovat nebo odmítnou případy, kdy naši partneři uplatňují legitimní zájem na využití vašich údajů, navštivte naši stránku pro dodavatele."
    },
    "sr-Cyrl": {
        "purpose_header": "Ми и наши партнери обрађујемо податке у следеће сврхе",
        "description": "Ми и наши __VENDOR_COUNT_LINK__ партнери користимо колачиће и сличне методе за препознавање наших посетилаца и памћење њихових поставки. Такође можемо користити ове технологије за процену ефикасности рекламних кампања, циљање реклама и анализу саобраћаја на вебсајту. Неке од ових технологија су од суштинског значаја за обезбеђивање правилног функционисања услуге или вебсајта и не могу се онемогућити, док су друге изборне, али служе за побољшање корисничког искуства на различите начине. \n\nУ сарадњи са нашим __VENDOR_COUNT_LINK__ партнерима, ми чувамо информације и/или им приступамо на корисниковом уређају, што укључује, између осталог, IP адресе, јединствене идентификаторе и податке о прегледању сачуване у колачићима, како бисмо обрађивали личне податке. Имате опцију да управљате својим подешавањима тако што ћете изабрати опцију „Управљање подешавањима“ која се налази у подножју странице. Да бисте прегледали или уложили приговор на случајеве у којима наши партнери тврде да имају легитиман интерес за коришћење ваших података, посетите нашу страницу добављача."
    },
    "ru": {
        "purpose_header": "Мы с партнерами обрабатываем данные в следующих целях",
        "description": "Мы с партнерами __VENDOR_COUNT_LINK__ используем файлы cookie и аналогичные методы для распознавания посетителей и запоминания их предпочтений. Мы также можем использовать эти технологии для оценки эффективности рекламных кампаний, целевой рекламы и анализа посещаемости сайта. Некоторые из этих технологий необходимы для обеспечения надлежащего функционирования сервиса или сайта. Их нельзя отключить. Другие необязательны, но помогают улучшить пользовательский опыт различными способами. \n\nВ сотрудничестве со своими партнерами __VENDOR_COUNT_LINK__ мы храним информацию на устройстве пользователя и (или) обращаемся к ней для обработки персональных данных. К этой информации относятся, помимо прочего, IP-адреса, уникальные идентификаторы и данные о просмотре сайтов, хранящиеся в файлах cookie. Вы можете управлять своими настройками, выбрав «Управление настройками» в нижнем колонтитуле страницы. Узнать, в каких случаях наши партнеры заявляют о своем законном интересе в использовании ваших данных, или возразить против такого использования можно на странице, посвященной нашим поставщикам."
    },
    "sl": {
        "purpose_header": "Mi in naši partnerji obdelujemo podatke za naslednje namene",
        "description": "Mi in naši partnerji __VENDOR_COUNT_LINK__ uporabljamo piškotke in podobne metode, da prepoznamo obiskovalce in si zapomnimo njihove nastavitve. Te tehnologije lahko uporabljamo tudi za merjenje učinkovitosti oglaševalskih kampanj, ciljno usmerjanje oglasov in analizo prometa na spletnem mestu. Nekatere od teh tehnologij so nujne za zagotavljanje pravilnega delovanja storitve ali spletnega mesta in jih ni mogoče onemogočiti, medtem ko so druge neobvezne, vendar služijo za izboljšanje uporabniške izkušnje na različne načine. \n\nV sodelovanju z našimi partnerji __VENDOR_COUNT_LINK__ shranjujemo in/ali dostopamo do informacij na uporabnikovi napravi, kar med drugim vključuje naslove IP, edinstvene identifikatorje in podatke o brskanju, shranjene v piškotkih, z namenom obdelave osebnih podatkov. Svoje nastavitve lahko upravljate tako, da izberete možnost »Upravljanje nastavitev« v nogi strani. Če želite pregledati ali ugovarjati primerom, v katerih naši partnerji uveljavljajo zakoniti interes za uporabo vaših podatkov, obiščite našo stran o partnerjih."
    },
    "mt": {
        "purpose_header": "Aħna u l-imsieħba tagħna nipproċessaw id-dejta għall-iskopijiet li ġejjin",
        "description": "Aħna u l-imsieħba __VENDOR_COUNT_LINK__ tagħna nużaw il-cookies u metodi simili biex nagħrfu l-viżitaturi u niftakru l-preferenzi tagħhom. Nistgħu nużaw ukoll dawn it-teknoloġiji biex inkejlu l-effettività tal-kampanji ta’ reklamar, noħolqu reklami mmirati, u nanalizzaw in-numru ta’ żjarat fis-sit web. Xi wħud minn dawn it-teknoloġiji huma essenzjali biex jiġi żgurat il-funzjonament xieraq tas-servizz jew tas-sit web, b’hekk dawn ma jistgħux jiġu diżattivati, filwaqt li oħrajn mhumiex obbligatorji iżda jservu biex itejbu l-esperjenza tal-utent b’diversi modi. \n\nAħna, f’kollaborazzjoni mal-imsieħba __VENDOR_COUNT_LINK__ tagħna, naħżnu u/jew naċċessaw l-informazzjoni fuq l-apparat ta’ utent, li tinkludi iżda li mhijiex limitata għal indirizzi IP, identifikaturi uniċi, u dejta tal-ibbrawżjar maħżuna fil-cookies, sabiex nipproċessaw dejta personali. Għandek l-għażla li timmaniġġja l-preferenzi tiegħek billi tagħżel l-għażla ‘Immaniġġja l-Preferenzi’ li tinsab fil-qiegħ tal-paġna. Biex tirrevedi jew toġġezzjona għal każijiet fejn l-imsieħba tagħna jaffermaw interess leġittimu fl-użu tad-dejta tiegħek, jekk jogħġbok żur il-paġna tal-bejjiegħa tagħna."
    },
    "nl": {
        "purpose_header": "Wij en onze partners verwerken gegevens voor de volgende doeleinden",
        "description": "Wij en onze __VENDOR_COUNT_LINK__ partners gebruiken cookies en vergelijkbare methoden om bezoekers te herkennen en hun voorkeuren te onthouden. We kunnen deze technologieën ook gebruiken om de effectiviteit van advertentiecampagnes te meten, gericht te adverteren en websiteverkeer te analyseren. Sommige van deze technologieën zijn essentieel voor de juiste werking van de dienst of website en kunnen niet uitgeschakeld worden, terwijl andere optioneel zijn maar de gebruikerservaring op verschillende manieren verbeteren. \n\nWij, in samenwerking met onze __VENDOR_COUNT_LINK__ partners, bewaren en/of gebruiken informatie op het apparaat van een gebruiker, inclusief maar niet beperkt tot IP-adressen, unieke identificatiegegevens en in cookies bewaarde browsegegevens, om persoonlijke gegevens te verwerken. U kunt uw voorkeuren beheren door de optie 'Voorkeuren beheren' in de voettekst van de pagina te selecteren. Ga naar onze leverancierspagina als u wilt zien in welke gevallen onze partners zich beroepen op een gerechtvaardigd belang om uw gegevens te gebruiken of als u daar bezwaar tegen wilt maken."
    },
    "fi": {
        "purpose_header": "Me ja kumppanimme käsittelemme tietoja seuraaviin tarkoituksiin",
        "description": "Me ja __VENDOR_COUNT_LINK__ kumppanimme käytämme evästeitä ja vastaavia menetelmiä vierailijoiden tunnistamiseen ja heidän valintojensa muistamiseen. Voimme käyttää näitä tekniikoita myös mainoskampanjoiden tehokkuuden mittaamiseen, mainosten kohdistamiseen ja verkkosivuston liikenteen analysointiin. Jotkut näistä teknologioista ovat välttämättömiä palvelun tai verkkosivuston moitteettoman toiminnan varmistamiseksi, eikä niitä voi poistaa käytöstä. Toiset taas ovat valinnaisia, mutta ne parantavat käyttökokemusta eri tavoin. \n\nYhteistyössä __VENDOR_COUNT_LINK__ kumppaneidemme kanssa tallennamme käyttäjän laitteelle tietoja ja/tai käytämme niitä, mukaan lukien, mutta ei rajoittuen, IP-osoitteet, yksilölliset tunnisteet ja evästeisiin tallennetut selaustiedot henkilötietojen käsittelyä varten. Asetuksia voi hallita valitsemalla ”Hallinnoi asetuksia” -vaihtoehdon sivun alatunnisteessa. Toimittajasivullamme voi tarkastaa tai vastustaa tapauksia, joissa kumppanimme käyttävät oikeutettua etua tietojen hyödyntämiseen."
    },
    "en": {
        "purpose_header": "We and our partners process data for the following purposes",
        "description": "We and our __VENDOR_COUNT_LINK__ partners use cookies and similar methods to recognize visitors and remember their preferences. We may also use these technologies to gauge the effectiveness of advertising campaigns, target advertisements, and analyze website traffic. Some of these technologies are essential for ensuring the proper functioning of the service or website and cannot be disabled, while others are optional but serve to enhance the user experience in various ways. \n\nWe, in collaboration with our __VENDOR_COUNT_LINK__ partners, store and/or access information on a user's device, including but not limited to IP addresses, unique identifiers, and browsing data stored in cookies, in order to process personal data. You have the option to manage your preferences by selecting the 'Manage Preferences' option located in the page's footer. To review or object to instances where our partners assert a legitimate interest in utilizing your data, please visit our vendors page."
    }
}
# fmt: on


def upgrade():
    logger.info(
        f"Starting TCF Description Update and Addition of new Purpose Header {datetime.now()}"
    )

    bind = op.get_bind()

    # Getting details about the ExperienceTranslations along with their latest historical version
    # from ExperienceConfigHistory (every time a PrivacyExperienceConfig and/or an ExperienceTranslation is updated,
    # a new version is created in PrivacyExperienceConfigHistory).
    translation_and_latest_hist_join = bind.execute(
        text(
            """
        SELECT et.id as et_id, hist.id as hist_id, hist.version, et.language, et.description FROM experiencetranslation et
        JOIN privacyexperienceconfighistory hist ON et.id=hist.translation_id 
        WHERE hist.component = 'tcf_overlay'
        AND hist.version = (
            SELECT MAX(version) 
            FROM privacyexperienceconfighistory 
            WHERE translation_id=hist.translation_id
        );
        """
        )
    )

    for res in translation_and_latest_hist_join:
        if res["language"] in updated_translations:
            updated_translation = updated_translations[res["language"]]
            updated_translation["translation_id"] = res["et_id"]

            if res["version"] != 1:
                # Only update translation descriptions if there haven't been any edits
                updated_translation["description"] = res["description"]

            # For every ExperienceTranslation for which we have new data, add the purpose header,
            # in all cases, and update the description provided it's not a version 1
            bind.execute(
                text(
                    """
                    UPDATE experiencetranslation
                    SET description=:description, purpose_header=:purpose_header
                    WHERE id=:translation_id;
                    """
                ),
                updated_translation,
            )

            # Now to mimic what we do when a translation is updated, create a new ExperienceConfigHistory
            # record with the updated values and a bumped version.
            create_experience_config_history = text(
                """
                 INSERT INTO privacyexperienceconfighistory (
                        id,
                        component,
                        disabled,
                        is_default,
                        reject_button_label,
                        version,
                        accept_button_label,
                        acknowledge_button_label,
                        banner_enabled,
                        description, 
                        privacy_preferences_link_label,
                        privacy_policy_link_label,
                        privacy_policy_url,
                        save_button_label,
                        title, 
                        banner_description,
                        banner_title, 
                        language,
                        name,
                        origin,
                        dismissable,
                        auto_detect_language,
                        allow_language_selection,
                        translation_id,
                        modal_link_label,
                        show_layer1_notices,
                        layer1_button_options,
                        purpose_header
                 )
                 SELECT
                    :id,
                    component,
                    disabled,
                    is_default,
                    reject_button_label,
                    :version,
                    accept_button_label,
                    acknowledge_button_label,
                    banner_enabled,
                    :description, 
                    privacy_preferences_link_label,
                    privacy_policy_link_label,
                    privacy_policy_url,
                    save_button_label,
                    title, 
                    banner_description,
                    banner_title, 
                    language,
                    name,
                    origin,
                    dismissable,
                    auto_detect_language,
                    allow_language_selection,
                    translation_id,
                    modal_link_label,
                    show_layer1_notices,
                    layer1_button_options,
                    :purpose_header
                FROM privacyexperienceconfighistory
                WHERE id = :existing_historical_id;
                """
            )

            bind.execute(
                create_experience_config_history,
                {
                    "id": generate_record_id("pri"),
                    "version": res["version"] + 1,
                    "existing_historical_id": res["hist_id"],
                    "description": updated_translation["description"],
                    "purpose_header": updated_translation["purpose_header"],
                },
            )


def downgrade():
    pass
