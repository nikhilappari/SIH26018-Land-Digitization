import pytest
from app.services.extraction import MultilingualFieldExtractor, extract_fields
from app.services.normalization import normalize_date, normalize_area
from app.services.language import detect_language

@pytest.fixture
def extractor():
    return MultilingualFieldExtractor()

def test_null_safety_on_empty_text(extractor):
    """Verify that unextracted or missing fields strictly return None rather than invented data."""
    raw_ocr = {"text": "", "lines": []}
    structured, staging = extractor.extract_all(raw_ocr, 0.0)
    
    assert staging["owner_name"] is None
    assert staging["survey_number"] is None
    assert staging["village"] is None
    assert staging["khata_number"] is None
    assert staging["area"] is None
    assert staging["tehsil_mandal"] is None
    assert staging["district"] is None
    assert structured["owner_name"]["value"] is None
    assert structured["owner_name"]["confidence"] == 0.0

def test_telugu_land_record_extraction(extractor):
    """Verify complete extraction of a realistic Telugu land record."""
    telugu_ocr = {
        "text": '''
        ఆంధ్రప్రదేశ్ ప్రభుత్వం - రెవెన్యూ శాఖ
        పట్టాదారు పేరు: కొండ్రు రాము
        తండ్రి పేరు: కొండ్రు వెంకటయ్య
        సర్వే నంబరు: 124/2A
        ఖాతా నం: 356
        దరఖాస్తు నం: 217/2022
        తేది: 15/06/2022
        విస్తీర్ణం: 2.35 ఎకరాలు
        గ్రామము: పెద్దవెంకటాపురం
        మండలము: రాజమండ్రి గ్రామీణ
        జిల్లా: తూర్పుగోదావరి
        ''',
        "lines": []
    }
    structured, staging = extractor.extract_all(telugu_ocr, 90.0)
    
    assert staging["owner_name"] == "కొండ్రు రాము"
    assert staging["survey_number"] == "124/2A"
    assert staging["khata_number"] == "356"
    assert staging["registration_number"] == "217/2022"
    assert staging["registration_date"] == "2022-06-15"  # Normalized!
    assert structured["registration_date"]["original_value"] == "15/06/2022"
    assert staging["area"] == 2.35
    assert staging["area_unit"] == "Acres"
    assert staging["village"] == "Pedavenkatapuram"
    assert staging["tehsil_mandal"] == "Rajahmundry Rural"
    assert staging["district"] == "East Godavari"

def test_hindi_khasra_extraction(extractor):
    """Verify extraction of a North Indian Hindi revenue record."""
    hindi_ocr = {
        "text": '''
        उत्तर प्रदेश भू-अभिलेख
        खातेदार का नाम: रामेश सिंह
        पिता का नाम: सुंदर सिंह
        खसरा संख्या: 882/1
        खाता संख्या: 412
        कुल क्षेत्रफल: 1.50 हेक्टेयर
        ग्राम: हापुड़
        तहसील: मेरठ
        दिनांक: 10-08-2023
        ''',
        "lines": []
    }
    structured, staging = extractor.extract_all(hindi_ocr, 92.0)
    
    assert staging["owner_name"] == "रामेश सिंह"
    assert staging["khasra_number"] == "882/1"
    assert staging["khata_number"] == "412"
    assert staging["area"] == 1.50
    assert staging["area_unit"] == "Hectares"
    assert staging["village"] == "Hapur"
    assert staging["tehsil_mandal"] == "Meerut"
    assert staging["registration_date"] == "2023-08-10"

def test_tamil_patta_extraction(extractor):
    """Verify extraction of a Tamil Nadu Patta Chitta record."""
    tamil_ocr = {
        "text": '''
        தமிழ்நாடு நில உரிமை ஆவணம்
        பட்டாதாரர் பெயர்: கிருஷ்ணமூர்த்தி
        புல எண்: 145/3A
        பட்டா எண்: 504
        பரப்பளவு: 3.20 ஹெக்டேர்
        கிராமம்: சோழவந்தான்
        வட்டம்: மதுரை
        தேதி: 25.11.2021
        ''',
        "lines": []
    }
    structured, staging = extractor.extract_all(tamil_ocr, 88.0)
    
    assert staging["owner_name"] == "கிருஷ்ணமூர்த்தி"
    assert staging["survey_number"] == "145/3A"
    assert staging["khata_number"] == "504"
    assert staging["area"] == 3.20
    assert staging["area_unit"] == "Hectares"
    assert staging["village"] == "Sholavandan"
    assert staging["tehsil_mandal"] == "Madurai"
    assert staging["registration_date"] == "2021-11-25"

def test_english_survey_extraction(extractor):
    """Verify extraction of standard English land survey records."""
    english_ocr = {
        "text": '''
        GOVERNMENT OF ANDHRA PRADESH - REVENUE DEPARTMENT
        RECORD OF RIGHTS (ROR-1B)
        Owner Name: Kondru Ramu
        Survey Number: 145/3A
        Khata Number: 412
        Total Extent: 2.50 Acres
        Village: Krishnapuram
        Mandal: Pedapadu
        District: West Godavari
        Registration Number: 1042/2021
        Registration Date: 2021-04-12
        ''',
        "lines": []
    }
    structured, staging = extractor.extract_all(english_ocr, 95.0)
    
    assert staging["owner_name"] == "Kondru Ramu"
    assert staging["survey_number"] == "145/3A"
    assert staging["khata_number"] == "412"
    assert staging["area"] == 2.50
    assert staging["area_unit"] == "Acres"
    assert staging["village"] == "Krishnapuram"
    assert staging["tehsil_mandal"] == "Pedapadu"
    assert staging["district"] == "West Godavari"
    assert staging["registration_number"] == "1042/2021"
    assert staging["registration_date"] == "2021-04-12"

def test_mixed_language_record(extractor):
    """Verify extraction on mixed English + Regional script documents."""
    mixed_ocr = {
        "text": '''
        ANDHRA PRADESH REVENUE DEPARTMENT
        పట్టాదారు పేరు (Owner): Bandi Suresh
        Survey No / సర్వే నం: 123/4A
        Khata No: 789
        Extent / విస్తీర్ణం: 3.10 Acres
        Village: పెద్దవెంకటాపురం
        Date: 12/09/2020
        ''',
        "lines": []
    }
    structured, staging = extractor.extract_all(mixed_ocr, 90.0)
    
    assert "Bandi Suresh" in staging["owner_name"]
    assert staging["survey_number"] == "123/4A"
    assert staging["khata_number"] == "789"
    assert staging["area"] == 3.10
    assert staging["village"] == "Pedavenkatapuram"
    assert staging["registration_date"] == "2020-09-12"

def test_date_normalizations():
    """Verify that multiple Indian date formats normalize to YYYY-MM-DD."""
    d1 = normalize_date("15/06/2022")
    assert d1["normalized"] == "2022-06-15"
    assert d1["original"] == "15/06/2022"

    d2 = normalize_date("15-06-2022")
    assert d2["normalized"] == "2022-06-15"

    d3 = normalize_date("15.06.2022")
    assert d3["normalized"] == "2022-06-15"

    d4 = normalize_date("2022-06-15")
    assert d4["normalized"] == "2022-06-15"

    d5 = normalize_date("15 June 2022")
    assert d5["normalized"] == "2022-06-15"

def test_survey_number_string_formats(extractor):
    """Verify that complex survey numbers are preserved as raw strings."""
    for sy_str in ["124/2A", "124/2", "125/3", "12-15", "123/4A", "100/1"]:
        sample = f"Survey Number: {sy_str}\nOwner: Ramu"
        _, staging = extractor.extract_all({"text": sample, "lines": []}, 90.0)
        assert staging["survey_number"] == sy_str
        assert isinstance(staging["survey_number"], str)

def test_area_extent_formats():
    """Verify normalization of decimal, colon, and regional area formats."""
    a1 = normalize_area(None, source_text="2.35 acres")
    assert a1["value"] == 2.35
    assert a1["unit"] == "Acres"

    a2 = normalize_area(None, source_text="2:35")
    assert a2["value"] == 2.35

    a3 = normalize_area(None, source_text="2.35 ఎకరాలు")
    assert a3["value"] == 2.35
    assert a3["unit"] == "Acres"

    a4 = normalize_area(None, source_text="1.25 हेक्टेयर")
    assert a4["value"] == 1.25
    assert a4["unit"] == "Hectares"
