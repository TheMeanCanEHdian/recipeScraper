import os
import requests
import re
import yaml
from bs4 import BeautifulSoup
from collections import OrderedDict

# NOTE: This script requires Python 3

# Description:
# This script takes a Blue Apron or Hello Fresh reipe URL, scrape and saves it into a YAML file
# and saves the recipe image for use with Salt to Taste.

# Settings
testMode = False # Set to True to run against a test url
testURL = 'https://www.blueapron.com/recipes/sweet-spicy-udon-noodles-with-fried-eggs-vegetables'
defaultTags = ['meal'] # Enter your desired default tags
siteTag = True # Change to False if you do not want a 'blue apron' or 'hello fresh' tag
quickMealTag = True # Change to False if you do not want an extra tag added for quick meals
vegetarianTag = True # Change to False if you do not want an extra tag added for vegetarian meals
# HELLO FRESH ONLY
spicyTag = True # Change to False if you do not want an extra tag added for spicy meals
# End of settings

def grabBlueApron(url):
    recipe_dict = OrderedDict({
        'layout' : 'recipe',
        'title' : None,
        'image' : None,
        'imagecredit' : None,
        'tags' : defaultTags[:],
        'source' : url,
        'prep' : None,
        'cook' : None,
        'ready' : None,
        'servings' : None,
        'calories' : None,
        'description' : None,
        'ingredients' : [],
        'directions' : [],
        'notes' : []
    })

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    if r.status_code == 200:
        main_section = soup.find("section", class_="section-recipe recipe-main row")

        recipe_dict['title'] = f"{main_section.find('h1').text.strip()} {main_section.find('h2').text.strip()}"
        recipe_dict['ready'] = int(f"{main_section.find('span', class_='total-time').text.strip().split(' ')[0]}")
        recipe_dict['servings'] = int(f"{main_section.find('span', itemprop='recipeYield').text.strip()}")
        recipe_dict['calories'] = int(f"{main_section.find('span', itemprop='calories').text.strip()}")
        recipe_dict['description'] = f"{main_section.find('p', itemprop='description').text}"
        recipe_dict['imagecredit'] = f"{main_section.find('img')['src'].split('?')[0]}"

        if siteTag:
            recipe_dict['tags'].append('blue apron')
        if quickMealTag and recipe_dict['ready'] <= 20:
            recipe_dict['tags'].append("quick meal")

        badges = main_section.find_all('span', class_='culinary-badge')
        for badge in badges:
            if badge.text.strip() == "Vegetarian" and vegetarianTag:
                recipe_dict['tags'].append(badge.text.strip().lower())

        ingredients_section = soup.find_all('li', itemprop='recipeIngredient')
        for ingredient in ingredients_section:
            string = ''
            measurement = ingredient.span.text.strip().split('\n')
            string = string + f"{measurement[0]}"
            if len(measurement) > 1:
                string = string + f" {measurement[1]}"
            ingredient.span.decompose() # Removes span with measurement so ingredient.text returns only ingredient name
            ingredient = ingredient.text.strip()
            string = string + f" {ingredient}"
            recipe_dict['ingredients'].append(string.strip(' '))

        instructions_section = soup.find_all('div', itemprop='recipeInstructions', class_='p-15')
        for instruction in instructions_section:
            string = ''
            instruction.span.decompose() # Removes span with step number
            instruction = re.sub(r'\n+', '\n', instruction.text).strip().split('\n')
            recipe_dict['directions'].append(f"{instruction[0].strip(' ').strip(':')}; {instruction[1].strip(' ')}")
        return (recipe_dict)
    else:
        print (f'Error with URL. Status Code {r.status_code}')

def grabHelloFresh(url):
    recipe_dict = OrderedDict({
        'layout' : 'recipe',
        'title' : None,
        'image' : None,
        'imagecredit' : None,
        'tags' : defaultTags[:],
        'source' : url,
        'prep' : None,
        'cook' : None,
        'ready' : None,
        'servings' : 2,
        'calories' : None,
        'description' : None,
        'ingredients' : [],
        'directions' : [],
        'notes' : []
    })

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    if r.status_code == 200:
        recipe_dict['title'] = f"{soup.find('h1').text.strip()} {soup.find('h4').text.strip()}"
        recipe_dict['imagecredit'] = soup.find("img", class_="fela-_1b1idjb")['src'].split('?')[0]
        recipe_dict['prep'] = int(soup.find(string="Preparation Time").find_parent().find_parent().find_next_sibling().text.strip().split(' ')[0])
        recipe_dict['calories'] = int(soup.find(string="Calories").find_parent().find_next_sibling().text.strip(' kcal'))
        recipe_dict['description'] = soup.find("p").text.strip()

        if siteTag:
            recipe_dict['tags'].append('hello fresh')
        if vegetarianTag and soup.find("span", class_="fela-_36rlri", string="Veggie"):
            recipe_dict['tags'].append('vegetarian')
        if quickMealTag and soup.find("span", class_="fela-_fnl8w9", string="20-Min Meal"):
            recipe_dict['tags'].append('quick meal')
        if vegetarianTag and soup.find("span", class_="fela-_36rlri", string="Spicy"):
            recipe_dict['tags'].append('spicy')

        ingredients = soup.find_all("div", class_="fela-_1qz307e")
        for ingredient in ingredients:
            string = ""
            content = ingredient.find_all("p")
            measurement = content[0].text.strip().split(' ')
            string = string + f" {measurement[0]}"
            if len(measurement) > 1:
                string = string + f" {measurement[1]}"
            ingredient = content[1].text.strip()
            string = string + f" {ingredient}"
            recipe_dict['ingredients'].append(string.strip(' '))

        instructions = soup.find_all("div", class_="fela-_1qzip4i")
        for instruction in instructions:
            content = instruction.find("p").text.strip().replace(':', ';').replace('\n', ' ')
            recipe_dict['directions'].append(content)
        return (recipe_dict)
    else:
        print (f'Error with URL. Status Code {r.status_code}')

def saveRecipe(title, recipe_dict, directory="recipes"):
    title = title.replace(' ', '-').lower()
    file = os.path.join(directory, title + '.yaml')

    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(file, 'w', encoding='utf-8') as f:
        yaml.add_representer(OrderedDict, lambda dumper, data: dumper.represent_mapping('tag:yaml.org,2002:map', data.items()))
        yaml.dump(recipe_dict, f, allow_unicode=True, sort_keys=False)
        print (f"Saved file")

def downloadImage(recipe_dict, directory="images"):
    title_formatted = recipe_dict['title'].replace(' ', '-').lower()
    ext = recipe_dict['imagecredit'].rsplit('.', 1)[1]
    r = requests.head(recipe_dict['imagecredit'])

    if 'image' in r.headers.get('content-type'):
        r = requests.get(recipe_dict['imagecredit'])

        if not os.path.exists(directory):
            os.makedirs(directory)

        open(f'{directory}/{title_formatted}.{ext}', 'wb').write(r.content)
        print (f"Saved image")

    return f'{title_formatted}.{ext}'

def main():
    user_input = ''
    while user_input != 'exit':
        if testMode is False:
            user_input = input("Enter URL (exit to quit): \n").lower()
        else:
            print ("Executing test download")
            user_input = testURL
        if user_input != 'exit':
            helloFreshRecipe = True if re.search('.*hellofresh.com.*', user_input) else False
            blueApronRecipe = True if re.search('.*blueapron.com.*', user_input) else False

            if blueApronRecipe:
                recipe = grabBlueApron(user_input)
            elif helloFreshRecipe:
                recipe = grabHelloFresh(user_input)
            else:
                raise ValueError('URL was not for Hello Fresh or Blue Apron')
            print (f"Grabbed {recipe['title']}")
            image = downloadImage(recipe)
            recipe['image'] = image
            saveRecipe(recipe['title'], recipe)

            if testMode is True:
                break

if __name__ == "__main__":
    main()
