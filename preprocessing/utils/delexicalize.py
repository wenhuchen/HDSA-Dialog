import re

import simplejson as json

from .nlp import normalize

digitpat = re.compile('\d+')
timepat = re.compile("\d{1,2}[:]\d{1,2}")
pricepat2 = re.compile("\d{1,3}[.]\d{1,2}")

# FORMAT
# domain_value
# restaurant_postcode
# restaurant_address
# taxi_car8
# taxi_number
# train_id etc..
def prepareSlotValuesIndependent():
    domains = ['restaurant', 'hotel', 'attraction', 'train', 'hospital', 'police']
    dic = set()
    dic_area = []
    dic_food = []
    dic_price = []

    # read databases
    for domain in domains:
        fin = open('db/' + domain + '_db.json')
        db_json = json.load(fin)
        fin.close()

        for ent in db_json:
            for key, val in ent.items():
                if val == '?' or val == 'free':
                    pass
                elif key == 'address':
                    dic.add((normalize(val), '[{}_address]'.format(domain)))
                    if "road" in val:
                        val = val.replace("road", "rd")
                        dic.add((normalize(val),  '[{}_address]'.format(domain)))
                    elif "rd" in val:
                        val = val.replace("rd", "road")
                        dic.add((normalize(val),  '[{}_address]'.format(domain)))
                    elif "st" in val:
                        val = val.replace("st", "street")
                        dic.add((normalize(val),  '[{}_address]'.format(domain)))
                    elif "street" in val:
                        val = val.replace("street", "st")
                        dic.add((normalize(val),  '[{}_address]'.format(domain)))
                elif key == 'name':
                    dic.add((normalize(val),  '[{}_name]'.format(domain)))
                    if "b & b" in val:
                        val = val.replace("b & b", "bed and breakfast")
                        dic.add((normalize(val), '[{}_name]'.format(domain)))
                    elif "bed and breakfast" in val:
                        val = val.replace("bed and breakfast", "b & b")
                        dic.add((normalize(val), '[{}_name]'.format(domain)))
                    elif "hotel" in val and 'gonville' not in val:
                        val = val.replace("hotel", "")
                        dic.add((normalize(val), '[{}_name]'.format(domain)))
                    elif "restaurant" in val:
                        val = val.replace("restaurant", "")
                        dic.add((normalize(val), '[{}_name]'.format(domain)))
                elif key == 'postcode':
                    dic.add((normalize(val), '[{}_postcode]'.format(domain)))
                elif key == 'phone':
                    dic.add((val, '[{}_phone]'.format(domain)))
                elif key == 'trainid':
                    dic.add((normalize(val), '[{}_trainid]'.format(domain)))
                elif key == 'department':
                    dic.add((normalize(val), '[{}_department]'.format(domain)))

                # NORMAL DELEX
                elif key == 'area':
                    dic.add((normalize(val), '[{}_area]'.format(domain)))
                elif key == 'food':
                    dic.add((normalize(val), '[{}_food]'.format(domain)))
                elif key == 'pricerange':
                    dic.add((normalize(val), '[{}_pricerange]'.format(domain)))
                else:
                    pass
    
        if domain == 'hospital':
            dic.add((normalize('Hills Road'), '[' + domain + '_' + 'address' + ']'))
            dic.add(('01223245151', '[' + domain + '_' + 'phone' + ']'))
            dic.add(('1223245151', '[' + domain + '_' + 'phone' + ']'))
            dic.add(('0122324515', '[' + domain + '_' + 'phone' + ']'))
            
        if domain == 'police':
            dic.add((normalize('Parkside'), '[{}_name]'.format(domain)))
            dic.add(('01223358966', '[{}_phone]'.format(domain)))
            dic.add(('1223358966', '[{}_phone]'.format(domain)))
            dic.add((normalize('Parkside Police Station'), '[{}_name]'.format(domain)))

    # add at the end places from trains
    fin = open('db/' + 'train' + '_db.json')
    db_json = json.load(fin)
    fin.close()

    for ent in db_json:
        for key, val in ent.items():
            if key == 'departure':
                dic.add((normalize(val), '[value_place]'))
            #elif key == 'destination':
            #    dic.add((normalize(val), '[{}_destination]'.format("train")))
    
    # add specific values:
    for key in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
        dic.add((normalize(key), '[' + 'value' + '_' + 'day' + ']'))

    # more general values add at the end
    #dic.extend(dic_area)
    #dic.extend(dic_food)
    #dic.extend(dic_price)
    dic = sorted(dic, key=lambda x:len(x[0].split()), reverse=True)
    return dic


def delexicalise(utt, dictionary):
    for key, val in dictionary:
        utt = (' ' + utt + ' ').replace(' ' + key + ' ', ' ' + val + ' ')
        utt = utt[1:-1]  # why this?

    return utt


def delexicaliseDomain(utt, dictionary, domain):
    for key, val in dictionary:
        if key == domain or key == 'value':
            utt = (' ' + utt + ' ').replace(' ' + key + ' ', ' ' + val + ' ')
            utt = utt[1:-1]  # why this?

    # go through rest of domain in case we are missing something out?
    for key, val in dictionary:
        utt = (' ' + utt + ' ').replace(' ' + key + ' ', ' ' + val + ' ')
        utt = utt[1:-1]  # why this?
    return utt

if __name__ == '__main__':
    prepareSlotValuesIndependent()
