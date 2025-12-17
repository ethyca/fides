"""Add GPC translation fields to experience translations

Revision ID: f8a9b0c1d2e3
Revises: a7241db3ee6a
Create Date: 2025-12-15 12:00:00.000000

This migration adds 5 GPC (Global Privacy Control) translatable fields to the
ExperienceTranslation and PrivacyExperienceConfigHistory tables:
- gpc_label: "Global Privacy Control"
- gpc_description: Description shown when GPC preference is honored
- gpc_status_applied_label: "Applied"
- gpc_status_overridden_label: "Overridden"
- gpc_title: "Global Privacy Control detected"

These fields allow customization of GPC-related strings that were previously
static in FidesJS locale files.
"""

import sqlalchemy as sa
from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision = "f8a9b0c1d2e3"
down_revision = "a7241db3ee6a"
branch_labels = None
depends_on = None

# GPC translations from messages.json files (verbatim)
# fmt: off
GPC_TRANSLATIONS = {
    "ar": {
        "gpc_label": "التحكم العالمي في الخصوصية",
        "gpc_description": "تم تطبيق تفضيلك للتحكم العالمي في الخصوصية. لقد ألغي اشتراكك تلقائيًا في حالات استخدام البيانات التي تلتزم بالتحكم العالمي في الخصوصية.",
        "gpc_status_applied_label": "تم التطبيق",
        "gpc_status_overridden_label": "تم التجاوز",
        "gpc_title": "تم اكتشاف التحكم العالمي في الخصوصية",
    },
    "bg": {
        "gpc_label": "Глобално управление на личните данни",
        "gpc_description": "Вашето предпочитание за глобално управление на личните данни е зачетено. Вие сте били автоматично изключени от случаите на използване на данни, които се отнасят към глобално управление на личните данни.",
        "gpc_status_applied_label": "Приложено",
        "gpc_status_overridden_label": "Премахнато",
        "gpc_title": "Установен е глобален контрол на поверителността",
    },
    "bs": {
        "gpc_label": "Globalna kontrola privatnosti",
        "gpc_description": "Vaš izbor globalne kontrole privatnosti je uvažen. Automatski ste isključeni iz slučajeva korištenja podataka koji se pridržavaju globalne kontrole privatnosti.",
        "gpc_status_applied_label": "Prihvaćena",
        "gpc_status_overridden_label": "Odbijena",
        "gpc_title": "Globalna kontrola privatnosti je otkrivena",
    },
    "ca": {
        "gpc_label": "Control de privadesa global",
        "gpc_description": "S’ha respectat la vostra preferència pel que fa al control de privadesa global. Se us ha exclòs automàticament dels casos d’ús de dades que s’adhereixen al control de privadesa global.",
        "gpc_status_applied_label": "Aplicat",
        "gpc_status_overridden_label": "Anul·lat",
        "gpc_title": "S'ha detectat un control de privadesa global",
    },
    "cs": {
        "gpc_label": "Globální kontrola ochrany osobních údajů",
        "gpc_description": "Byly dodrženy vaše globální preference ochrany osobních údajů. Automaticky jste byli vyřazeni z používání údajů v případech, na které se vztahuje globální ochrana osobních údajů.",
        "gpc_status_applied_label": "Aplikováno",
        "gpc_status_overridden_label": "Přepsáno",
        "gpc_title": "Byla zjištěna globální kontrola soukromí",
    },
    "da": {
        "gpc_label": "Global fortrolighedskontrol",
        "gpc_description": "Din præference i forbindelse med global fortrolighedskontrol er blevet efterkommet. Du er automatisk blevet frameldt tilfælde af databrug, der overholder global fortrolighedskontrol.",
        "gpc_status_applied_label": "Anvendt",
        "gpc_status_overridden_label": "Tilsidesat",
        "gpc_title": "Global privatlivskontrol registreret",
    },
    "de": {
        "gpc_label": "Globale Datenschutzeinstellungen",
        "gpc_description": "Ihre globale Datenschutzeinstellungen werden berücksichtigt. Sie wurden automatisch von Anwendungsfällen ausgenommen, die nicht Ihren globalen Datenschutzeinstellungen unterliegen.",
        "gpc_status_applied_label": "Angewendet",
        "gpc_status_overridden_label": "Überschrieben",
        "gpc_title": "Globale Datenschutzkontrolle erkannt",
    },
    "el": {
        "gpc_label": "Καθολικός έλεγχος απορρήτου",
        "gpc_description": "Η προτίμησή σας για τον καθολικό έλεγχο απορρήτου έχει τηρηθεί. Έχετε εξαιρεθεί αυτόματα από περιπτώσεις χρήσης δεδομένων που συμμορφώνονται με τον καθολικό έλεγχο απορρήτου.",
        "gpc_status_applied_label": "Εφαρμόστηκε",
        "gpc_status_overridden_label": "Παρακάμφθηκε",
        "gpc_title": "Εντοπίστηκε ο καθολικός έλεγχος απορρήτου",
    },
    "en": {
        "gpc_label": "Global Privacy Control",
        "gpc_description": "Your global privacy control preference has been honored. You have been automatically opted out of data use cases which adhere to global privacy control.",
        "gpc_status_applied_label": "Applied",
        "gpc_status_overridden_label": "Overridden",
        "gpc_title": "Global Privacy Control detected",
    },
    "es": {
        "gpc_label": "Control de privacidad global",
        "gpc_description": "Su preferencia de control de privacidad global se ha respetado. Se le ha excluido automáticamente de los casos de uso de datos que se adhieren al control de privacidad global.",
        "gpc_status_applied_label": "Aplicado",
        "gpc_status_overridden_label": "Anulado",
        "gpc_title": "Control de privacidad global detectado",
    },
    "es-MX": {
        "gpc_label": "Control de privacidad global",
        "gpc_description": "Su preferencia de control de privacidad global se ha respetado. Se le excluyó automáticamente de los casos de uso de datos que se adhieren al control de privacidad global.",
        "gpc_status_applied_label": "Aplicado",
        "gpc_status_overridden_label": "Anulado",
        "gpc_title": "Control de privacidad global detectado",
    },
    "et": {
        "gpc_label": "Üldine andmekaitsekontroll",
        "gpc_description": "Teie üldist andmekaitse-eelistust on arvestatud. Teid on automaatselt välja arvatud andmete kasutamise juhtudest, mis järgivad üldist andmekaitsekontrolli.",
        "gpc_status_applied_label": "Rakendatud",
        "gpc_status_overridden_label": "Tühistatud",
        "gpc_title": "Tuvastati globaalne privaatsuskontroll",
    },
    "eu": {
        "gpc_label": "Pribatutasun-kontrol globala",
        "gpc_description": "Pribatutasun-kontrol globalaren lehentasuna bete da. Pribatutasun-kontrol globalari atxikitzen zaizkion datuen erabileren kasuetatik automatikoki baztertua izan zara.",
        "gpc_status_applied_label": "Ezarrita",
        "gpc_status_overridden_label": "Baliogabetuta",
        "gpc_title": "Pribatutasun-kontrol globala atzeman da",
    },
    "fi": {
        "gpc_label": "Maailmanlaajunen tietosuojavalvonta",
        "gpc_description": "Maailmanlaajuinen tietosuojavalvontanne on vahvistettu. Teidät on automaattisesti poistettu tietojen käyttötapauksista, jotka noudattavat maailmanlaajuista tietosuojavalvontaa.",
        "gpc_status_applied_label": "Käytössä",
        "gpc_status_overridden_label": "Ohitettu",
        "gpc_title": "Yleinen tietosuoja-asetus havaittu",
    },
    "fr": {
        "gpc_label": "Global Privacy Control",
        "gpc_description": "Votre préférence en matière de contrôle global de la confidentialité (GPC) a été respectée. Vous avez automatiquement été retiré des cas d’usage des données qui adhèrent au GPC.",
        "gpc_status_applied_label": "Appliqué",
        "gpc_status_overridden_label": "Ignoré",
        "gpc_title": "Contrôle global de la confidentialité détecté",
    },
    "fr-CA": {
        "gpc_label": "Contrôle mondial de confidentialité",
        "gpc_description": "Votre préférence en matière de contrôle mondial de confidentialité a été honorée. Vous avez été automatiquement écarté des cas d'utilisation de données qui adhèrent au contrôle mondial de confidentialité.",
        "gpc_status_applied_label": "Appliqué",
        "gpc_status_overridden_label": "Annulé",
        "gpc_title": "Contrôle de la confidentialité global détecté",
    },
    "gl": {
        "gpc_label": "Control de privacidade global",
        "gpc_description": "Respetouse a súa preferencia de control de privacidade global. Foi automaticamente excluído dos casos de uso de datos que cumpren o control de privacidade global.",
        "gpc_status_applied_label": "Aplicado",
        "gpc_status_overridden_label": "Anulado",
        "gpc_title": "Detectouse un control de privacidade global",
    },
    "hi-IN": {
        "gpc_label": "वैश्विक गोपनीयता नियंत्रण",
        "gpc_description": "आपकी वैश्विक गोपनीयता नियंत्रण वरीयताओं का सम्मान किया गया। आपको वैश्विक गोपनीयता नियंत्रण का पालन करने वाले डेटा उपयोग मामलों से स्वचालित रूप से बाहर कर दिया गया है।",
        "gpc_status_applied_label": "लागू किया",
        "gpc_status_overridden_label": "ओवरराइड किया",
        "gpc_title": "वैश्विक गोपनीयता नियंत्रण का पता चला",
    },
    "hr": {
        "gpc_label": "Globalna kontrola privatnosti",
        "gpc_description": "Poštuju se vaše preferencije globalne kontrole privatnosti. Automatski se isključeni iz slučajeve korištenja podataka koji se pridržavaju globalne kontrole privatnosti.",
        "gpc_status_applied_label": "Primijenjeno",
        "gpc_status_overridden_label": "Premošćeno",
        "gpc_title": "Otkrivena je globalna kontrola privatnosti",
    },
    "hu": {
        "gpc_label": "Globális adatvédelmi szabályozás",
        "gpc_description": "A globális adatvédelmi szabályozással kapcsolatos beállításai el lettek fogadva. Automatikusan kikerült azokból az adatfelhasználási esetekből, amelyek a globális adatvédelmi szabályozáshoz tartoznak.",
        "gpc_status_applied_label": "Alkalmazva",
        "gpc_status_overridden_label": "Felülírva",
        "gpc_title": "Globális adatvédelmi ellenőrzés észlelve",
    },
    "it": {
        "gpc_label": "Controllo Globale della Privacy",
        "gpc_description": "Le tue preferenze del Controllo Globale della Privacy sono state prese in carico. Sei stato automaticamente escluso dai casi di utilizzo dei dati che corrispondono al Controllo Globale della Privacy.",
        "gpc_status_applied_label": "Applicato",
        "gpc_status_overridden_label": "Non applicato",
        "gpc_title": "Rilevato il controllo della privacy globale",
    },
    "ja": {
        "gpc_label": "グローバルプライバシーコントロール",
        "gpc_description": "グローバルプライバシーコントロールの設定は尊重されます。グローバルプライバシーコントロールに従うデータのユースケースからは自動的にオプトアウトされています。",
        "gpc_status_applied_label": "適用",
        "gpc_status_overridden_label": "変更",
        "gpc_title": "グローバルプライバシー管理を検出しました",
    },
    "lt": {
        "gpc_label": "Visuotinė privatumo kontrolė",
        "gpc_description": "Buvo atsižvelgta į jūsų visuotinės privatumo kontrolės pageidavimą. Buvote automatiškai atšauktas iš duomenų naudojimo atvejų, kai laikomasi visuotinės privatumo kontrolės.",
        "gpc_status_applied_label": "Taikoma",
        "gpc_status_overridden_label": "Nebegaliojantis",
        "gpc_title": "Aptiktas visuotinis privatumo valdymas",
    },
    "lv": {
        "gpc_label": "Globālā privātuma kontrole",
        "gpc_description": "Mēs esam izpildījuši jūsu prasību kontrolēt globālo privātumu. Pēc noklusējuma esat noņemts no datu lietojuma pieteikumiem, kas atbilst globālajai privātuma kontrolei.",
        "gpc_status_applied_label": "Pielietots",
        "gpc_status_overridden_label": "Ignorēts",
        "gpc_title": "Konstatēta globālā privātuma kontrole",
    },
    "mt": {
        "gpc_label": "Kontroll Globali tal-Privatezza",
        "gpc_description": "Il-preferenza globali tiegħek għall-kontroll tal-privatezza ġiet onorata. Inti awtomatikament għażilt li ma tibqax tuża d-dejta f'każijiet li jirrispettaw il-kontroll globali tal-privatezza.",
        "gpc_status_applied_label": "Applikat",
        "gpc_status_overridden_label": "Maqbuża",
        "gpc_title": "Kontroll Globali tal-Privatezza misjub",
    },
    "nl": {
        "gpc_label": "Global Privacy Control",
        "gpc_description": "Uw Global Privacy Control-voorkeur wordt gerespecteerd. U bent automatisch afgemeld voor gegevensgebruiksscenario's die zich houden aan Global Privacy Control.",
        "gpc_status_applied_label": "Toegepast",
        "gpc_status_overridden_label": "Genegeerd",
        "gpc_title": "Globale privacyinstelling gedetecteerd",
    },
    "no": {
        "gpc_label": "Globale personverninnstillinger",
        "gpc_description": "Preferansene dine vedrørende de globale personverninnstilingene dine er godtatt. Du har automatisk takket nei til databruksaker som følger globale personverninnstillinger.",
        "gpc_status_applied_label": "Anvendt",
        "gpc_status_overridden_label": "Overstyrt",
        "gpc_title": "Global personvernkontroll oppdaget",
    },
    "pl": {
        "gpc_label": "Ogólna kontrola prywatności",
        "gpc_description": "Twoja preferencja dotycząca ogólnej kontroli prywatności została uwzględniona. Automatycznie odmówiono zgody na Twoje przypadki wykorzystania danych, które są zgodne z Ogólną kontrolą prywatności.",
        "gpc_status_applied_label": "Zastosowano",
        "gpc_status_overridden_label": "Nadpisano",
        "gpc_title": "Wykryto globalną kontrolę prywatności",
    },
    "pt-BR": {
        "gpc_label": "Controle de Privacidade Global",
        "gpc_description": "Sua preferência global de controle de privacidade foi respeitada. Você foi automaticamente removido dos casos de uso de dados que aderem ao controle de privacidade global.",
        "gpc_status_applied_label": "Aplicado",
        "gpc_status_overridden_label": "Anulado",
        "gpc_title": "Controle de Privacidade Global detectado",
    },
    "pt-PT": {
        "gpc_label": "Controlo de Privacidade Global",
        "gpc_description": "A sua preferência de controlo de privacidade global foi honrada. Foi automaticamente excluído/a dos casos de utilização de dados que aderem ao controlo de privacidade global.",
        "gpc_status_applied_label": "Aplicado",
        "gpc_status_overridden_label": "Anulado",
        "gpc_title": "Controlo de Privacidade Global detetado",
    },
    "ro": {
        "gpc_label": "Control global al confidențialității",
        "gpc_description": "Preferința dvs. de control global al confidențialității a fost onorată. Ați fost exclus(ă) automat de la cazurile de utilizare a datelor care respectă controlul global al confidențialității.",
        "gpc_status_applied_label": "Aplicat",
        "gpc_status_overridden_label": "Suprascris",
        "gpc_title": "S-a detectat controlul global al confidențialității",
    },
    "ru": {
        "gpc_label": "Global Privacy Control",
        "gpc_description": "Ваша настройка Global Privacy Control учтена. Вы автоматически исключаетесь в сценариях, где используется Global Privacy Control.",
        "gpc_status_applied_label": "Применено",
        "gpc_status_overridden_label": "Изменено",
        "gpc_title": "Обнаружена глобальная система контроля конфиденциальности",
    },
    "sk": {
        "gpc_label": "Globálna kontrola súkromia",
        "gpc_description": "Vaša predvoľba pre globálnu kontrolu súkromia bola dodržaná. Pre prípady použitia, kde sa používa globálna kontrola súkromia, vám bol automaticky nastavený explicitný nesúhlas.",
        "gpc_status_applied_label": "Použitá",
        "gpc_status_overridden_label": "Prepísaná",
        "gpc_title": "Zistila sa globálna kontrola ochrany osobných údajov",
    },
    "sl": {
        "gpc_label": "Global Privacy Control",
        "gpc_description": "Vaša nastavitev globalnega nadzora zasebnosti je bila upoštevana. Samodejno je bilo preklicano vaše soglasje za tiste primere uporabe podatkov, ki se ravnajo po globalnem nadzoru zasebnosti.",
        "gpc_status_applied_label": "Uporabljeno",
        "gpc_status_overridden_label": "Preglašeno",
        "gpc_title": "Zaznan je globalni nadzor nad zasebnostjo",
    },
    "sr-Cyrl": {
        "gpc_label": "Global Privacy Control",
        "gpc_description": "Ваша глобална поставка контроле приватности је подешена. Аутоматски сте искључени из случајева употребе података који су у складу са глобалном контролом приватности.",
        "gpc_status_applied_label": "Примењена",
        "gpc_status_overridden_label": "Замењена",
        "gpc_title": "Откривена је глобална контрола приватности",
    },
    "sr-Latn": {
        "gpc_label": "Globalna kontrola privatnosti",
        "gpc_description": "Vaša globalna postavka kontrole privatnosti se poštuje. Automatski ste isključeni iz slučajeva korišćenja podataka koji podležu globalnoj kontroli privatnosti.",
        "gpc_status_applied_label": "Primenjeno",
        "gpc_status_overridden_label": "Zaobiđeno",
        "gpc_title": "Otkrivena je globalna kontrola privatnosti",
    },
    "sv": {
        "gpc_label": "Global integritetskontroll",
        "gpc_description": "Dina preferenser för global integritetskontroll har efterföljts. Du har automatiskt valt bort användningsfall för uppgifter som efterföljer global integritetskontroll.",
        "gpc_status_applied_label": "Tillämpad",
        "gpc_status_overridden_label": "Åsidosatt",
        "gpc_title": "Global sekretesskontroll upptäcktes",
    },
    "tr": {
        "gpc_label": "Global Gizlilik Kontrolü",
        "gpc_description": "Global gizlilik kontrolü tercihiniz yerine getirildi. Global gizlilik kontrolüne uygun veri kullanım durumlarından otomatik olarak çıkarıldınız.",
        "gpc_status_applied_label": "Uygulandı",
        "gpc_status_overridden_label": "Geçersiz kılındı",
        "gpc_title": "Genel Gizlilik Kontrolü algılandı",
    },
    "uk": {
        "gpc_label": "Глобальний контроль конфіденційності",
        "gpc_description": "Ваші налаштування глобального контролю конфіденційності враховано. Вас було автоматично виключено з випадків використання даних, які дотримуються налаштувань глобального контролю конфіденційності.",
        "gpc_status_applied_label": "Застосовано",
        "gpc_status_overridden_label": "Перевизначено",
        "gpc_title": "Виявлено глобальний контроль конфіденційності",
    },
    "zh": {
        "gpc_label": "全局隐私控制",
        "gpc_description": "您的全局隐私控制偏好已得到尊重。您已自动选择退出符合全局隐私控制的数据使用案例。",
        "gpc_status_applied_label": "已应用",
        "gpc_status_overridden_label": "被覆盖",
        "gpc_title": "检测到全局隐私控制",
    },
    "zh-Hant": {
        "gpc_label": "全域隱私控制",
        "gpc_description": "您的全域隱私控制偏好已被接受。根據您的選擇·，已自動將您退出符合全域隱私控制的資料使用案例。",
        "gpc_status_applied_label": "已應用",
        "gpc_status_overridden_label": "已覆寫",
        "gpc_title": "檢測到全局隱私控制",
    },
}
# fmt: on

# English fallback for any language not in the dict
EN_FALLBACK = GPC_TRANSLATIONS["en"]


def upgrade():
    # Add GPC columns to experiencetranslation table
    op.add_column(
        "experiencetranslation",
        sa.Column("gpc_label", sa.String(), nullable=True),
    )
    op.add_column(
        "experiencetranslation",
        sa.Column("gpc_description", sa.String(), nullable=True),
    )
    op.add_column(
        "experiencetranslation",
        sa.Column("gpc_status_applied_label", sa.String(), nullable=True),
    )
    op.add_column(
        "experiencetranslation",
        sa.Column("gpc_status_overridden_label", sa.String(), nullable=True),
    )
    op.add_column(
        "experiencetranslation",
        sa.Column("gpc_title", sa.String(), nullable=True),
    )

    # Add GPC columns to privacyexperienceconfighistory table
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("gpc_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("gpc_description", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("gpc_status_applied_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("gpc_status_overridden_label", sa.String(), nullable=True),
    )
    op.add_column(
        "privacyexperienceconfighistory",
        sa.Column("gpc_title", sa.String(), nullable=True),
    )

    # Populate default GPC values for all existing translations
    connection = op.get_bind()

    # Get all distinct languages in the DB
    result = connection.execute(
        sa.text("SELECT DISTINCT language FROM experiencetranslation")
    )
    languages_in_db = [row[0] for row in result]

    for language in languages_in_db:
        # Use language-specific translations if available, otherwise English
        translations = GPC_TRANSLATIONS.get(language, EN_FALLBACK)
        update_result = connection.execute(
            sa.text(
                """
                UPDATE experiencetranslation
                SET gpc_label = :gpc_label,
                    gpc_description = :gpc_description,
                    gpc_status_applied_label = :gpc_status_applied_label,
                    gpc_status_overridden_label = :gpc_status_overridden_label,
                    gpc_title = :gpc_title
                WHERE language = :language
                """
            ),
            {**translations, "language": language},
        )
        if update_result.rowcount > 0:
            logger.info(
                f"Updated {update_result.rowcount} experience translation(s) "
                f"for language '{language}' with GPC defaults"
            )


def downgrade():
    # Drop columns from privacyexperienceconfighistory
    op.drop_column("privacyexperienceconfighistory", "gpc_title")
    op.drop_column("privacyexperienceconfighistory", "gpc_status_overridden_label")
    op.drop_column("privacyexperienceconfighistory", "gpc_status_applied_label")
    op.drop_column("privacyexperienceconfighistory", "gpc_description")
    op.drop_column("privacyexperienceconfighistory", "gpc_label")

    # Drop columns from experiencetranslation
    op.drop_column("experiencetranslation", "gpc_title")
    op.drop_column("experiencetranslation", "gpc_status_overridden_label")
    op.drop_column("experiencetranslation", "gpc_status_applied_label")
    op.drop_column("experiencetranslation", "gpc_description")
    op.drop_column("experiencetranslation", "gpc_label")
