import os, requests, json, re
from bs4 import BeautifulSoup

#NOTE: This script requires Python 3

#Description:
#This script takes a Blue Apron or Hello Fresh reipe URL and scrapes it into a text or mardown format
#and saves the recipe images for use in Salt to Taste or Chowdown.

#Settings
testMode = False #Set to True to run against a test url
testURL = 'https://www.blueapron.com/recipes/sweet-spicy-udon-noodles-with-fried-eggs-vegetables'
defaultTags = ['meal'] #Enter your desired default tags
siteTag = True #Change to False if you do not want a 'blue apron' or 'hello fresh' tag
vegetarianTag = True #Change to False if you do not want an extra tag added for vegetarian meals
quickMealTag = True #Change to False if you do not want an extra tag added for quick meals
extraRecipeInfo = True #Set to False to only grab the Chowdown defaults (True to save extra information like servings and calories for Salt to Taste)
saveAsMD = False #Set to True to save as a markdown (.md) file for use with Chowdown (False to save as .txt for use with Salt to Taste)
#End of settings

def grabBlueApron(url):
    recipe_dict = {'url':url, 'main':{}, 'ingredients':[], 'instructions':[]}
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    if r.status_code is 200:
        #main section
        main_section = soup.find("section", class_="section-recipe recipe-main row")
        if main_section.find('svg', class_='icon-svg icon-svg--veg'):
            recipe_dict['main'].update({'meal_vegetarian':True})
            main_section.find('svg', class_='icon-svg icon-svg--veg').decompose()
        else:
            recipe_dict['main'].update({'meal_vegetarian':False})
        quickmeal = main_section.find('span', class_='is-quickmeal')
        if quickmeal is not None:
            recipe_dict['main'].update({'meal_quick':True})
        else:
            recipe_dict['main'].update({'meal_quick':False})
        recipe_dict['main'].update({'title_main':main_section.find("h1").text.strip(), 'title_sub':main_section.find("h2").text.strip(), 'meal_time':main_section.find('div', class_='ba-info-list__item-value').text.strip(), 'meal_servings':main_section.find('span', itemprop='recipeYield').text.strip(), 'meal_calories':main_section.find('span', itemprop='calories').text.strip(), 'meal_description':main_section.find('p', itemprop='description').text, 'meal_image':main_section.find('img')["src"]})
        #ingredient section
        ingredients_section = soup.find_all('li', itemprop='recipeIngredient')
        for ingredient in ingredients_section:
            dict = {}
            measurement = ingredient.span.text.strip().split('\n')
            dict.update(amount = measurement[0])
            if len(measurement) > 1:
                dict.update(unit = measurement[1])
            ingredient.span.decompose() #removes span with measurement so ingredient.text returns only ingredient name
            ingredient = ingredient.text.strip()
            dict.update(ingredient = ingredient)
            recipe_dict['ingredients'].append(dict)
        #instructions section
        instructions_section = soup.find_all('div', itemprop='recipeInstructions', class_='p-15')
        for instruction in instructions_section:
            dict = {}
            instruction.span.decompose() #removes span with step number
            instruction = re.sub(r'\n+', '\n', instruction.text).strip().split('\n')
            dict.update(title = instruction[0].rstrip(' ').strip(':')) #remove colon from instruction title
            dict.update(text = instruction[1])
            recipe_dict['instructions'].append(dict)
        return (recipe_dict)
    else:
        print (f'Error with URL. Status Code {r.status_code}')

def grabHelloFresh(url):
    recipe_dict = {'url':url, 'main':{}, 'ingredients':[], 'instructions':[]}
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    if r.status_code is 200:
        title = soup.find("h1").text.strip()
        subtitle = soup.find("h4").text.strip()
        time = soup.find(string="Preparation Time").find_parent().find_parent().find_next_sibling().text.strip()
        calories = soup.find(string="Calories").find_parent().find_next_sibling().text.strip(' kcal')
        description = soup.find("p").text.strip()
        image = soup.find("img", class_="fela-_1b1idjb")['src']
        vegetarian = True if soup.find("span", class_="fela-_36rlri", string="Veggie") else False
        quick_meal = True if soup.find("span", class_="fela-_fnl8w9", string="20-Min Meal") else False

        recipe_dict['main'].update({'title_main':title, 'title_sub':subtitle, 'meal_time':time, 'meal_servings':2, 'meal_calories':calories, 'meal_description':description, 'meal_image':image, 'meal_vegetarian': vegetarian, 'meal_quick': quick_meal})

        ingredients = soup.find_all("div", class_="fela-_1qz307e")
        for ingredient in ingredients:
            dict = {}
            content = ingredient.find_all("p")
            measurement = content[0].text.strip().split(' ')
            dict.update(amount = measurement[0])
            if len(measurement) > 1:
                dict.update(unit = measurement[1])
            ingredient = content[1].text.strip()
            dict.update(ingredient = ingredient)
            recipe_dict['ingredients'].append(dict)

        instructions = soup.find_all("div", class_="fela-_1qzip4i")
        for instruction in instructions:
            content = instruction.find("p").text.strip().replace(':', ';').replace('\n', ' ')
            recipe_dict['instructions'].append(content)

        return (recipe_dict)
    else:
        print (f'Error with URL. Status Code {r.status_code}')

def saveRecipe(recipe_dict, blueApronRecipe = False):
    if blueApronRecipe:
        tags = defaultTags[:]
        if siteTag:
            tags.append('blue apron')
    else:
        tags = defaultTags[:]
        if siteTag:
            tags.append('hello fresh')
    formatted_title = f'{recipe_dict["main"]["title_main"]} {recipe_dict["main"]["title_sub"]}'.replace(" ", "_").lower()
    if os.path.exists('_recipes') is False:
        os.makedirs('_recipes')
    if saveAsMD:
        f = open(f'_recipes/{formatted_title}.md', 'w+', encoding='utf-16')
        f.write('---\n\n')
    else:
        f = open(f'_recipes/{formatted_title}.txt', 'w+', encoding='utf-16')
    f.write('layout: recipe\n')
    f.write(f'title: "{recipe_dict["main"]["title_main"]} {recipe_dict["main"]["title_sub"]}"\n')
    f.write(f'image: {formatted_title}.jpg\n')
    if vegetarianTag is True and recipe_dict["main"]["meal_vegetarian"] is True:
        tags.append('vegetarian')
    if quickMealTag is True and recipe_dict["main"]["meal_quick"] is True:
        tags.append('quick meal')
    f.write(f'imagecredit: {recipe_dict["main"]["meal_image"]}\n')
    f.write(f'tags: {", ".join(tags)}\n')
    if extraRecipeInfo is True:
        f.write(f'source: {recipe_dict["url"]}\n')
        f.write('\nprep: \n')
        f.write('cook: \n')
        f.write(f'ready: {recipe_dict["main"]["meal_time"]}\n')
        f.write(f'servings: {recipe_dict["main"]["meal_servings"]}\n')
        f.write(f'calories: {recipe_dict["main"]["meal_calories"]}\n\n')
        f.write(f'description: \n{recipe_dict["main"]["meal_description"].replace(":", ";")}\n')
    f.write('\ningredients: \n')
    for ingredient in recipe_dict['ingredients']:
        string = '-'
        for key in ingredient.keys():
            if ingredient[key]:
                string = string + f' {ingredient[key]}'
        f.write(f'{string}\n')

    f.write('\ndirections: \n')
    for instruction in recipe_dict["instructions"]:
        if blueApronRecipe:
            f.write(f'- {instruction["title"]}; {instruction["text"]}\n')
        else:
            f.write(f'- {instruction}\n')
    if extraRecipeInfo is True:
        f.write('\nnotes: \n')
    if saveAsMD:
        f.write('\n---')
    f.close()

def downloadImages(recipe_dict):
    formatted_title = f'{recipe_dict["main"]["title_main"]} {recipe_dict["main"]["title_sub"]}'.replace(" ", "_").lower()
    if os.path.exists('images') is False:
        os.makedirs('images')
    r = requests.get(recipe_dict['main']['meal_image'])
    open(f'images/{formatted_title}.jpg', 'wb').write(r.content)

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
            print ("Grabbed recipe")
            saveRecipe(recipe, blueApronRecipe)
            print ("Saved recipe")
            downloadImages(recipe)
            print ("Downloaded images")
            if testMode is True:
                break

if __name__ == "__main__":
    main()
