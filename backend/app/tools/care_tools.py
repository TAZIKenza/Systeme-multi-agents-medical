from langchain_core.tools import tool


@tool
def recommend_interim_care(symptoms_summary: str) -> str:
    """
    Genere une recommandation intermediaire de soins basee sur un resume des symptomes.
    Cette recommandation est prudente et generale, en attente de validation medicale.
    """
    base_recommendations = [
        "Repos suffisant et arret des activites physiques intenses.",
        "Hydratation reguliere (au minimum 1,5 litre d'eau par jour).",
        "Surveillance de l'evolution des symptomes.",
        "Consulter rapidement un medecin en cas d'aggravation des symptomes.",
        "Eviter l'automédication sans avis medical."
    ]

    recommendation = "Recommandations intermediaires de precaution :\n"
    for i, rec in enumerate(base_recommendations, 1):
        recommendation += f"{i}. {rec}\n"

    recommendation += "\nATTENTION : Ces recommandations sont generales et ne remplacent pas un avis medical professionnel."
    return recommendation
