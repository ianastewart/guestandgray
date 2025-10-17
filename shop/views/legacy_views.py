from django.shortcuts import render, get_object_or_404, redirect


def legacy_view(request, page):
    if ".html" in page:
        page = page.split(".")[0]
    try:
        url = REDIRECTS[page]
    except KeyError:
        url = "/pages/"
    return redirect(url, permanent=True)


REDIRECTS = {
    "19": "/pages/information/about-us/",
    "9": "/catalogue/",
    "13": "/pages/information/making-a-purchase/",
    "28": "/SELLING/",
    "16": "/pages/information/antique-chinese-ceramics-and-works-of-art/",
    "156": "/bibliography/",
    "820": "/pages/information/reviews/",
    "30": "/pages/information/museum-links-and-useful-websites/",
    "11": "/contact",
    "Chinese-Ming-Ceramics": "/catalogue/chinese/ming-and-earlier/",
    "Chinese_Kangxi_Blue_and_White": "/catalogue/chinese/qing-porcelain/kangxi-blue-and-white/",
    "Antique-Chinese-Famille-Verte-Porcelain": "/catalogue/chinese/qing-porcelain/famille-verte-porcelain/",
    "Catalogue_Chinese_Imperial__Blanc_de_Chine___Monochromes_18": "/catalogue/chinese/imperial-monochromes/",
    "Chinese_Armorial_Porcelain": "/catalogue/chinese/armorial-porcelain/",
    "Catalogue_Chinese_Imari_57": "/catalogue/chinese/qing-porcelain/imari/",
    "Chinese_Famille-Rose_Porcelain": "/catalogue/chinese/qing-porcelain/imari/",
    "Catalogue_Chinese_Famille_Rose_Tea_Wares_2": "/catalogue/chinese/qing-porcelain/famille-rose-teawares/",
    "Catalogue_Chinese_Blue___White_Qing_Porcelain_33": "/catalogue/chinese/qing-porcelain/blue-and-white-porcelain/",
    "Chinese-Qing-Works-Art": "/catalogue/chinese/qing-works-of-art/",
    "Catalogue_Chinese_Snuff_Bottles_104": "/catalogue/chinese/snuff-bottles/",
    "Catalogue_Japanese_Porcelain_127": "/catalogue/japanese/japanese-porcelain/",
    "Japanese_Works_of_Art": "/catalogue/japanese/works-of-art/",
    "Catalogue_Islamic_and_Indian_Art_40": "/catalogue/japanese/islamic-and-indian-art/",
    "Chinese_Paintings": "/catalogue/chinese/drawings/",
    "Catalogue_European_Glass_35": "/catalogue/european/glass/",
    "Catalogue_European_Porcelain_52": "/catalogue/european/porcelain/",
    "Catalogue_European_Works_of_Art_and_Furniture_37": "/catalogue/european/works-of-art-and-furniture/",
    "antique-european-pottery": "/catalogue/european/pottery/",
    "Antique_Jewellery": "/catalogue/other/antique-jewellery-silver/",
    "Dutch-Delft": "/catalogue/european/pottery/dutch-delft/",
}
