# Parser3Dnews
Mod parser news from the site 3dnews for TorrentPier-II version 2.1.5 alpha
It's possible to re-upload pictures to your picture hosting, only supports Chevereto.

System requirements:

python3 and above with BeautifulSoup and PyMySQL libraries installed

Install:

/*** create table in database ***/

CREATE TABLE `bb_news_grab` (
 `id` INT(11) NOT NULL AUTO_INCREMENT,
 `import_id` INT(11) NOT NULL,
 PRIMARY KEY (`id`),
 INDEX `import_id` (`import_id`)
)
COLLATE='utf8_general_ci'
ENGINE=MyISAM
AUTO_INCREMENT=47;

/*** Cron task run every 15 min ***/

/usr/bin/python3 /home/main.py

the main.py file should be located in the home folder or in any convenient place
