import os, requests, json, re
from bs4 import BeautifulSoup

#NOTE: This script requires Python 3

#Description:
#This script takes a BLue Apron reipe URL and scrapes it into a markdown format and saves the recipe (and ingredient) images for use in Chowdown.
#If the recipe is vegetarian a

#Settings
testMode = False #Set to True to run against a test url
defaultTags = ['meal','blue apron'] #Enter your desired default tags
vegetarianTag = True #Change to False if you do not want an extra tag added for vegetarian meals
quickMealTag = True #Change to False if you do not want an extra tag added for quick meals
downloadIngredientImage = True #Set to True to download the extra ingredient image (False to just download the recipe image)
extraRecipeInfo = True #Set to True to save extra information like servings and nutrition (False to only grab the Chowdown defaults)
#End of settings



def grabRecipe(url):
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
        recipe_dict['main'].update({'title_main':main_section.find("h1").text.strip(), 'title_sub':main_section.find("h2").text.strip(), 'meal_time':main_section.find('div', class_='ba-info-list__item-value').text.strip(), 'meal_servings':main_section.find('span', itemprop='recipeYield').text.strip(), 'meal_nutrition':main_section.find('span', itemprop='calories').text.strip(), 'meal_description':main_section.find('p', itemprop='description').text, 'meal_image':main_section.find('img')["src"]})
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
        ingredients_image = soup.find('div', class_='ba-feature-image ingredients-img-hldr col-md-8').find('img')['src']
        recipe_dict['main'].update({'ingredients_image':ingredients_image})
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
        print ('Error with URL. Status Code {}'.format(r.status_code))

def saveRecipe(recipe_dict):
    tags = defaultTags[:]
    formatted_title = '{} {}'.format(recipe_dict['main']['title_main'], recipe_dict['main']['title_sub']).replace(" ", "_").lower()
    if os.path.exists('_recipes') is False:
        os.makedirs('_recipes')
    f = open('_recipes/{}.md'.format(formatted_title), 'w+', encoding='utf-8')
    f.write('---\n')
    f.write('\nlayout: recipe\n')
    f.write('title: "{} {}"\n'.format(recipe_dict['main']['title_main'], recipe_dict['main']['title_sub']))
    f.write('image: {}.jpg\n'.format(formatted_title))
    if vegetarianTag is True and recipe_dict['main']['meal_vegetarian'] is True:
        tags.append('vegetarian')
    if quickMealTag is True and recipe_dict['main']['meal_quick'] is True:
        tags.append('quick meal')
    f.write('imagecredit: {}\n'.format(recipe_dict['main']['ingredients_image']))
    f.write('tags: {}\n'.format(', '.join(tags)))
    if extraRecipeInfo is True:
        f.write('source: {}\n'.format(recipe_dict['url']))
        f.write('\nprep: \n')
        f.write('cook: \n')
        f.write('ready: {}\n'.format(recipe_dict['main']['meal_time']))
        f.write('servings: {}\n'.format(recipe_dict['main']['meal_servings']))
        f.write('nutrition: {} calories\n\n'.format(recipe_dict['main']['meal_nutrition']))
        f.write('description: \n{}\n'.format(recipe_dict['main']['meal_description'].replace(':', ';')))
    f.write('\ningredients: \n')
    for ingredient in recipe_dict['ingredients']:
        if 'unit' in ingredient.keys():
            f.write('- {} {} {}\n'.format(ingredient['amount'], ingredient['unit'], ingredient['ingredient']))
        else:
            f.write('- {} {}\n'.format(ingredient['amount'], ingredient['ingredient']))
    f.write('\ndirections: \n')
    for instruction in recipe_dict['instructions']:
        f.write('- {}; {}\n'.format(instruction['title'], instruction['text']))
    if extraRecipeInfo is True:
        f.write('\nnotes: \n')
    f.write('\n---')
    f.close()

def downloadImages(recipe_dict):
    formatted_title = '{} {}'.format(recipe_dict['main']['title_main'], recipe_dict['main']['title_sub']).replace(" ", "_").lower()
    if os.path.exists('images') is False:
        os.makedirs('images')
    r = requests.get(recipe_dict['main']['meal_image'])
    open('images/{}.jpg'.format(formatted_title), 'wb').write(r.content)
    if downloadIngredientImage is True:
        r = requests.get(recipe_dict['main']['ingredients_image'])
        open('images/{}_ingredients.jpg'.format(formatted_title), 'wb').write(r.content)

def main():
    user_input = ''
    while user_input != 'exit':
        if testMode is False:
            user_input = input("Enter URL (exit to quit): \n").lower()
        else:
            user_input = 'https://www.blueapron.com/recipes/sweet-spicy-udon-noodles-with-fried-eggs-vegetables'
        if user_input != 'exit':
            recipe = grabRecipe(user_input)
            print ("Grabbed recipe")
            saveRecipe(recipe)
            print ("Saved recipe")
            downloadImages(recipe)
            print ("Downloaded images")
            if testMode is True:
                break

if __name__ == "__main__":
    main()
