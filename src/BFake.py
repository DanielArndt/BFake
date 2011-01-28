
 
# BFake.py
# 
# Copyright (C) 2010 Daniel Arndt
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from selenium import selenium
import time, random, csv, sys


#Configuration stuff
MIN_PAGES = 1 #Minimum pages to open in a single browser session
MAX_PAGES = 10 #Maximum pages to open in a single browser session
MIN_LINKS = 0 #Minimum links to follow on a single webpage
MAX_LINKS = 10 #Maximum links to follow on a single webpage
LOGNORM_TIME_SPENT = True
MAX_ATTEMPTS_SERVERCONNECT = 3 #How many time to try connecting to selenium
MAX_ATTEMPTS_FINDLINK = 5 #How many times to try finding a link to follow

################################################################################

urls_list = []

def rand_time_spent():
    if (LOGNORM_TIME_SPENT):
        #roughly 30 seconds/page
        #random.lognormvariate(3.401197382, 0.9) If over 540 try again? 
        randomTime = 0
        while ((randomTime < 0.5) or (randomTime > 240)):
            #roughly 20 seconds/page
            randomTime = random.lognormvariate(2.9957325, 0.8)
        return randomTime
    else:
        return (3.0 + random.random() * 7.0)


def get_rand_URL():
    # Choose a random index with heavier weight towards the beginning
    url = ""
    url_suffix = ""
    random_index = 0
    # Avoid using website not in (.com,.net,.org) domain to
    # avoid... bad things...
    while ((url_suffix != "com") and 
           (url_suffix != "net") and
           (url_suffix != "org")):
        random_index = int(random.triangular(0, len(urls_list)-1, 0))
        url = urls_list[random_index].strip()
        url_split = url.split('.')
        url_suffix = url_split[len(url_split)-1]
    print "Selecting website number %d: %s" % (random_index, url)
    return url

################################################################################
def main():
    #Gather arguments
    #Open a reader for the URL list
    csvreader = csv.reader(open(sys.argv[1], "rb"))
    for line in csvreader:
        urls_list.append("http://" + line[1]) 
    sel_port = int(sys.argv[2])
    # Begin
    print "Read in %d websites from %s" % (len(urls_list), sys.argv[1])
    current_url = get_rand_URL()
    print "current_url = %s" % (current_url)
    #Set up server
    sel = selenium("localhost", sel_port, "*firefox", current_url)
    for attempts in range(MAX_ATTEMPTS_SERVERCONNECT):
        try:
            sel.start()
            break
        except Exception as e:
            print e
            if (attempts > MAX_ATTEMPTS_SERVERCONNECT-2):
                print "Failed after %s attempts" % (MAX_ATTEMPTS_SERVERCONNECT)
                return 1
            else:
                print "Trying again in 5 seconds."
                time.sleep(5) 
        
    #This JavaScript randomly selects a link from the browser and return the string
    #name of it.
    #ref: http://blog.browsermob.com/2009/08/how-to-get-selenium-to-follow-random-links/
    get_randomlink_javascript = "var temp = eval_xpath('//a\', window.document);\n"+"temp[Math.floor(Math.random() * temp.length)].innerHTML"
    print "Starting BFake at URL %s." % (current_url)
    success = False
    num_pages_to_browse = random.randint(MIN_PAGES,MAX_PAGES)
    num_links_to_follow = random.randint(MIN_LINKS,MAX_LINKS)
    for _ in range(num_pages_to_browse-1):
        print "Opening window at %s." % (current_url)
        try:
            sel.open(current_url)
        except Exception as e:
            print e
            current_url = get_rand_URL()
            continue
        print "Following %d links on %s." % (num_links_to_follow, current_url)
        for link_num in range(num_links_to_follow):
            print "Currently visiting link %d of %d." % (link_num+1, num_links_to_follow+1)
            failed_attempts = 0
            while not success:
                try:
                    linktext = sel.get_eval(get_randomlink_javascript)
                    sleeptime = rand_time_spent()
                    print "Waiting for %s seconds before following link %s." % (sleeptime, linktext)
                    time.sleep(sleeptime)
                    sel.click("link="+linktext.encode('utf-8'))
                    page_loadtime = random.randrange(20000,40000)
                    print "Will wait %d milliseconds for page to load." % (page_loadtime)
                    sel.wait_for_page_to_load(str(page_loadtime))
                    success = True
                    print "Following link %s succeeded" % (linktext)
                except Exception as e:
                    failed_attempts += 1
                    print "Following link %s failed, failed attempts: %d." % (linktext.encode('utf-8'), failed_attempts)
                    print str(e).encode('utf-8')
                    if failed_attempts > 4:
                        print "Failed too many times, exiting."
                        sel.stop()
                        return 1
            success = False 
        #Add something to close all windows?
    print "Done visiting all websites and links in this instance. Exiting."
    #Close the server, exit browser, close all connections to and proxy.
    sel.stop()
    return 0

if __name__ == "__main__":
    print "Exiting with status: %d" % (main())

