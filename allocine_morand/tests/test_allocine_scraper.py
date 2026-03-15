"""Tests unitaires pour AllocineScraper (fonctions sans Selenium)."""
import pandas as pd
from bs4 import BeautifulSoup
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers de fixtures HTML
# ---------------------------------------------------------------------------

def _make_film_soup(
    titre: str = "Mon Film",
    realisateur: str = "Jean Réal",
    note_presse: str = "3,5",
    note_spec: str = "4,2",
    synopsis: str = "Un synopsis.",
    platforms: list[str] | None = None,
    score_reco: str = "85",
    date: str = "12 mars 2024",
) -> BeautifulSoup:
    """Génère un HTML minimal simulant une page film Allociné."""
    platforms = platforms or []
    platform_html = (
        f'<div id="ovw-products">{" ".join(platforms)}</div>'
        if platforms
        else ""
    )
    html = f"""
    <html><body>
      <h1 class="title-entity">{titre}</h1>
      <div class="meta-body-direction"><a>{realisateur}</a></div>
      <div class="meta-body-info">
        <span class="date">{date}</span>
      </div>
      <span class="stareval-note">{note_presse}</span>
      <span class="stareval-note">{note_spec}</span>
      <p class="content-txt">{synopsis}</p>
      <span class="dZ6Qx4goXRfseGsQ2h8g">{score_reco}</span>
      {platform_html}
    </body></html>
    """
    return BeautifulSoup(html, "html.parser")


_DEFAULT_FILM_URL = (
    "https://www.allocine.fr/film/fichefilm_gen_cfilm=123456.html"
)


def _make_thumbnail_soup(url: str = _DEFAULT_FILM_URL) -> BeautifulSoup:
    """Génère un élément <figure class="thumbnail"> avec un lien."""
    html = (
        f'<figure class="thumbnail">'
        f'<a class="thumbnail-link" href="{url}"></a>'
        f"</figure>"
    )
    return BeautifulSoup(html, "html.parser")


# ---------------------------------------------------------------------------
# Tests _extract_director
# ---------------------------------------------------------------------------

class TestExtractDirector:
    def _scraper(self):
        """Crée un AllocineScraper avec driver mocké."""
        with patch("allocine_scraper.webdriver.Chrome"):
            from allocine_scraper import AllocineScraper
            s = AllocineScraper.__new__(AllocineScraper)
            s.driver = MagicMock()
            s.wait = MagicMock()
            return s

    def test_should_return_director_from_meta_body_direction(self):
        scraper = self._scraper()
        soup = _make_film_soup(realisateur="Stanley Kubrick")
        assert scraper._extract_director(soup) == "Stanley Kubrick"

    def test_should_return_none_when_no_director_found(self):
        scraper = self._scraper()
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        assert scraper._extract_director(soup) is None

    def test_should_fallback_to_meta_body_item_contains(self):
        scraper = self._scraper()
        html = """
        <html><body>
          <div class="meta-body-item">
            Réalisateur : <a>Christopher Nolan</a>
          </div>
        </body></html>
        """
        soup = BeautifulSoup(html, "html.parser")
        assert scraper._extract_director(soup) == "Christopher Nolan"


# ---------------------------------------------------------------------------
# Tests _extract_release_date
# ---------------------------------------------------------------------------

class TestExtractReleaseDate:
    def _scraper(self):
        with patch("allocine_scraper.webdriver.Chrome"):
            from allocine_scraper import AllocineScraper
            s = AllocineScraper.__new__(AllocineScraper)
            s.driver = MagicMock()
            s.wait = MagicMock()
            return s

    def test_should_return_date_from_span_date(self):
        scraper = self._scraper()
        soup = _make_film_soup(date="15 janvier 2023")
        result = scraper._extract_release_date(soup)
        assert result == "15 janvier 2023"

    def test_should_return_none_when_no_date(self):
        scraper = self._scraper()
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        assert scraper._extract_release_date(soup) is None


# ---------------------------------------------------------------------------
# Tests save_to_csv (sans Selenium)
# ---------------------------------------------------------------------------

class TestSaveToCSV:
    def _scraper(self):
        with patch("allocine_scraper.webdriver.Chrome"):
            from allocine_scraper import AllocineScraper
            s = AllocineScraper.__new__(AllocineScraper)
            s.driver = MagicMock()
            s.wait = MagicMock()
            return s

    def test_should_write_csv_with_correct_columns(self, tmp_path):
        scraper = self._scraper()
        films = [
            {
                "titre": "Inception",
                "realisateur": "Christopher Nolan",
                "date_sortie": "21 juillet 2010",
                "synopsis": "Un voleur de rêves.",
                "note_presse": "4.0",
                "note_spectateurs": "4.5",
                "score_recommandation": "92",
                "plateformes": "Netflix, Disney+",
                "url": "https://allocine.fr/film/1",
            }
        ]
        output = str(tmp_path / "test.csv")
        scraper.save_to_csv(films, filename=output)

        df = pd.read_csv(output, sep=";", encoding="utf-8-sig")
        assert "Titre" in df.columns
        assert "Netflix" in df.columns
        assert "Disney+" in df.columns
        assert df.iloc[0]["Titre"] == "Inception"
        assert df.iloc[0]["Netflix"] == "X"
        assert df.iloc[0]["Disney+"] == "X"

    def test_should_not_write_when_films_is_empty(self, tmp_path):
        scraper = self._scraper()
        output = str(tmp_path / "empty.csv")
        scraper.save_to_csv([], filename=output)
        assert not (tmp_path / "empty.csv").exists()

    def test_should_mark_absent_platform_as_empty(self, tmp_path):
        scraper = self._scraper()
        films = [
            {
                "titre": "Film A",
                "realisateur": "X",
                "date_sortie": "2020",
                "synopsis": "...",
                "note_presse": "3.0",
                "note_spectateurs": "3.5",
                "score_recommandation": "70",
                "plateformes": "Netflix",
                "url": "https://allocine.fr/film/2",
            },
            {
                "titre": "Film B",
                "realisateur": "Y",
                "date_sortie": "2021",
                "synopsis": "...",
                "note_presse": "Non disponible",
                "note_spectateurs": "4.0",
                "score_recommandation": "Non disponible",
                "plateformes": "Disney+",
                "url": "https://allocine.fr/film/3",
            },
        ]
        output = str(tmp_path / "multi.csv")
        scraper.save_to_csv(films, filename=output)

        # pandas lit les cellules vides comme NaN — fillna pour normaliser
        df = pd.read_csv(
            output, sep=";", encoding="utf-8-sig", keep_default_na=False
        )
        # Film A n'est pas sur Disney+
        assert df.loc[df["Titre"] == "Film A", "Disney+"].iloc[0] == ""
        # Film B n'est pas sur Netflix
        assert df.loc[df["Titre"] == "Film B", "Netflix"].iloc[0] == ""


# ---------------------------------------------------------------------------
# Tests FilmsVusScraper._get_existing_films_count
# ---------------------------------------------------------------------------

class TestGetExistingFilmsCount:
    def _scraper(self):
        with patch("allocine_scraper.webdriver.Chrome"):
            from films_vus_scraper import FilmsVusScraper
            s = FilmsVusScraper.__new__(FilmsVusScraper)
            s.driver = MagicMock()
            s.wait = MagicMock()
            return s

    def test_should_return_zero_when_file_absent(self, tmp_path):
        scraper = self._scraper()
        import allocine_scraper as base_mod
        original = base_mod.OUTPUT_DIR
        base_mod.OUTPUT_DIR = tmp_path
        import films_vus_scraper as fvs_mod
        fvs_mod.OUTPUT_DIR = tmp_path
        try:
            result = scraper._get_existing_films_count()
            assert result == 0
        finally:
            base_mod.OUTPUT_DIR = original
            fvs_mod.OUTPUT_DIR = original

    def test_should_return_correct_count_when_file_exists(self, tmp_path):
        scraper = self._scraper()
        import films_vus_scraper as fvs_mod
        original = fvs_mod.OUTPUT_DIR
        fvs_mod.OUTPUT_DIR = tmp_path

        # Créer un CSV de test
        csv_path = tmp_path / "films_vus_allocine.csv"
        df = pd.DataFrame(
            [{"Titre": "Film 1"}, {"Titre": "Film 2"}, {"Titre": "Film 3"}]
        )
        df.to_csv(csv_path, sep=";", encoding="utf-8-sig", index=False)

        try:
            result = scraper._get_existing_films_count()
            assert result == 3
        finally:
            fvs_mod.OUTPUT_DIR = original


# ---------------------------------------------------------------------------
# Tests is_chrome_running_with_debug_port
# ---------------------------------------------------------------------------

class TestIsChromeRunning:
    def test_should_return_true_when_chrome_with_debug_port(self):
        from allocine_scraper import is_chrome_running_with_debug_port
        import psutil

        mock_proc = MagicMock()
        mock_proc.info = {
            "name": "chrome.exe",
            "cmdline": ["chrome.exe", "--remote-debugging-port=9222"],
        }
        with patch.object(psutil, "process_iter", return_value=[mock_proc]):
            assert is_chrome_running_with_debug_port() is True

    def test_should_return_false_when_chrome_without_debug_port(self):
        from allocine_scraper import is_chrome_running_with_debug_port
        import psutil

        mock_proc = MagicMock()
        mock_proc.info = {
            "name": "chrome.exe",
            "cmdline": ["chrome.exe"],
        }
        with patch.object(psutil, "process_iter", return_value=[mock_proc]):
            assert is_chrome_running_with_debug_port() is False

    def test_should_return_false_when_no_process(self):
        from allocine_scraper import is_chrome_running_with_debug_port
        import psutil

        with patch.object(psutil, "process_iter", return_value=[]):
            assert is_chrome_running_with_debug_port() is False
