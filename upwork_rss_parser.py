import csv
import os.path
import time
import datetime
import requests
from bs4 import BeautifulSoup, NavigableString


def get_articles_from_rss(url, seen_articles):
    articles = []
    req = requests.get(url)
    src = req.content
    soup = BeautifulSoup(src, "xml")
    for item in soup.find_all("item"):
        item_url = item.find("link").text
        if item_url in seen_articles:
            continue
        details = find_details_in_description(item.find("description").text)
        articles.append(
            {
                "title": item.find("title").text,
                "link": item_url,
                "description": details["content"],
                "skills": details["skills"],
                "date": details["date"],
                "budget": details["budget"],
                "country": details["country"],
            }
        )
        seen_articles.add(item_url)
    return articles


def find_details_in_description(description):
    date_of_publication = None
    skills = None
    budget_range = None
    country = None

    soup = BeautifulSoup(description, "html.parser")

    def get_data_after_label(label):
        label_tag = soup.find("b", string=lambda s: label in s)
        if label_tag:
            for sibling in label_tag.next_siblings:
                if sibling.string and sibling.string.strip() != "":
                    return sibling.string[1:].strip()
        return None

    def get_data_before_label(label):
        label_tag = soup.find("b", string=lambda s: label in s)
        content_strings = []
        for element in label_tag.previous_siblings:
            if isinstance(element, NavigableString):
                content_strings.append(element.string.strip())
        return " ".join(reversed(content_strings))

    date_of_publication = get_data_after_label("Posted On")
    skills_string = get_data_after_label("Skills")
    skills = (
        ", ".join([skill.strip() for skill in skills_string.split(",")])
        if skills_string
        else None
    )
    budget_string = get_data_after_label("Hourly Range")
    budget_range = (
        tuple(map(str.strip, budget_string.split("-")))
        if budget_string and "-" in budget_string
        else None
    )
    country = get_data_after_label("Country")
    content_before_posted_on = get_data_before_label("Posted On")
    content_splited = content_before_posted_on.split(":")
    if "$" in content_splited[-1]:
        content_before_posted_on = "".join(content_splited[:-1]).strip()
        budget_range = content_splited[-1].strip()
    return {
        "content": content_before_posted_on,
        "skills": skills,
        "date": date_of_publication,
        "budget": budget_range,
        "country": country,
    }


def add_articles_to_csv(articles, file_name):
    fieldnames = ["title", "link", "description", "skills", "date", "budget", "country"]
    write_header = False
    if not os.path.isfile(file_name):
        write_header = True

    with open(file_name, "a", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        if write_header:
            writer.writeheader()
        writer.writerows(articles)


if __name__ == "__main__":
    url = "https://www.upwork.com/ab/feed/jobs/rss?sort=recency"
    seen_articles = set()
    today_date = datetime.date.today()
    rss_name = "upwork"
    for _ in range(60 * 24):
        articles = get_articles_from_rss(url, seen_articles)
        add_articles_to_csv(articles, f"{rss_name}_{today_date}.csv")
        print(datetime.datetime.now(), "file updated")
        time.sleep(60)
    print("finished")
