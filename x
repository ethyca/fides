man(1)                                                                  man(1)



NNAAMMEE
       man - format and display the on-line manual pages

SSYYNNOOPPSSIISS
       mmaann  [--aaccddffFFhhkkKKttwwWW]  [----ppaatthh]  [--mm _s_y_s_t_e_m] [--pp _s_t_r_i_n_g] [--CC _c_o_n_f_i_g___f_i_l_e]
       [--MM _p_a_t_h_l_i_s_t] [--PP _p_a_g_e_r] [--BB _b_r_o_w_s_e_r] [--HH _h_t_m_l_p_a_g_e_r] [--SS  _s_e_c_t_i_o_n___l_i_s_t]
       [_s_e_c_t_i_o_n] _n_a_m_e _._._.


DDEESSCCRRIIPPTTIIOONN
       mmaann formats and displays the on-line manual pages.  If you specify _s_e_c_-
       _t_i_o_n, mmaann only looks in that section of the manual.  _n_a_m_e  is  normally
       the  name of the manual page, which is typically the name of a command,
       function, or file.  However, if _n_a_m_e contains  a  slash  (//)  then  mmaann
       interprets  it  as a file specification, so that you can do mmaann ..//ffoooo..55
       or even mmaann //ccdd//ffoooo//bbaarr..11..ggzz.

       See below for a description of where mmaann  looks  for  the  manual  page
       files.


MMAANNUUAALL SSEECCTTIIOONNSS
       The standard sections of the manual include:

       11      User Commands

       22      System Calls

       33      C Library Functions

       44      Devices and Special Files

       55      File Formats and Conventions

       66      Games et. Al.

       77      Miscellanea

       88      System Administration tools and Deamons

       Distributions  customize  the  manual section to their specifics, which
       often include additional sections.


OOPPTTIIOONNSS
       --CC  ccoonnffiigg__ffiillee
              Specify  the  configuration  file  to  use; the default is //pprrii--
              vvaattee//eettcc//mmaann..ccoonnff.  (See mmaann..ccoonnff(5).)

       --MM  ppaatthh
              Specify the list of directories to search for man pages.   Sepa-
              rate  the directories with colons.  An empty list is the same as
              not specifying --MM at all.  See SSEEAARRCCHH PPAATTHH FFOORR MMAANNUUAALL PPAAGGEESS.

       --PP  ppaaggeerr
              Specify which pager to use.  This option overrides the  MMAANNPPAAGGEERR
              environment  variable,  which  in turn overrides the PPAAGGEERR vari-
              able.  By default, mmaann uses //uussrr//bbiinn//lleessss --iiss.

       --BB     Specify which browser to use on HTML files.  This  option  over-
              rides  the  BBRROOWWSSEERR  environment  variable. By default, mmaann uses
              //uussrr//bbiinn//lleessss-is,,

       --HH     Specify a command that renders HTML files as text.  This  option
              overrides  the  HHTTMMLLPPAAGGEERR  environment variable. By default, mmaann
              uses //bbiinn//ccaatt,

       --SS  sseeccttiioonn__lliisstt
              List is a colon separated list of  manual  sections  to  search.
              This option overrides the MMAANNSSEECCTT environment variable.

       --aa     By default, mmaann will exit after displaying the first manual page
              it finds.  Using this option forces mmaann to display all the  man-
              ual pages that match nnaammee,, not just the first.

       --cc     Reformat  the  source man page, even when an up-to-date cat page
              exists.  This can be meaningful if the cat  page  was  formatted
              for  a screen with a different number of columns, or if the pre-
              formatted page is corrupted.

       --dd     Don't actually display the man  pages,  but  do  print  gobs  of
              debugging information.

       --DD     Both display and print debugging info.

       --ff     Equivalent to wwhhaattiiss.

       --FF or ----pprreeffoorrmmaatt
              Format only - do not display.

       --hh     Print a help message and exit.

       --kk     Equivalent to aapprrooppooss.

       --KK     Search  for  the  specified  string in *all* man pages. Warning:
              this is probably very slow!  It  helps  to  specify  a  section.
              (Just  to  give  a  rough idea, on my machine this takes about a
              minute per 500 man pages.)

       --mm  ssyysstteemm
              Specify an alternate set of man pages to  search  based  on  the
              system name given.

       --pp  ssttrriinngg
              Specify  the  sequence  of  preprocessors to run before nnrrooffff or
              ttrrooffff.  Not all installations will have a full set of preproces-
              sors.   Some of the preprocessors and the letters used to desig-
              nate them are: eqn (e), grap (g), pic (p), tbl (t), vgrind  (v),
              refer  (r).   This  option  overrides the MMAANNRROOFFFFSSEEQQ environment
              variable.

       --tt     Use //uussrr//bbiinn//ggrrooffff --TTppss --mmaannddoocc --cc to format  the  manual  page,
              passing  the  output  to  ssttddoouutt..   The default output format of
              //uussrr//bbiinn//ggrrooffff --TTppss --mmaannddoocc --cc is Postscript, refer to the  man-
              ual  page  of //uussrr//bbiinn//ggrrooffff --TTppss --mmaannddoocc --cc for ways to pick an
              alternate format.

       Depending on the selected  format  and  the  availability  of  printing
       devices,  the  output  may  need  to  be  passed through some filter or
       another before being printed.

       --ww or ----ppaatthh
              Don't actually display the man pages, but  do  print  the  loca-
              tion(s) of the files that would be formatted or displayed. If no
              argument is given: display (on stdout) the list  of  directories
              that  is  searched by mmaann for man pages. If mmaannppaatthh is a link to
              man, then "manpath" is equivalent to "man --path".

       --WW     Like -w, but print file names one per line,  without  additional
              information.   This is useful in shell commands like mmaann --aaWW mmaann
              || xxaarrggss llss --ll


CCAATT PPAAGGEESS
       Man will try to save the formatted man pages, in order to save  format-
       ting time the next time these pages are needed.  Traditionally, format-
       ted versions of pages in DIR/manX are saved in DIR/catX, but other map-
       pings   from   man   dir   to   cat  dir  can  be  specified  in  //pprrii--
       vvaattee//eettcc//mmaann..ccoonnff.  No cat pages are saved when the required cat direc-
       tory  does  not  exist.  No cat pages are saved when they are formatted
       for a line length different from 80.   No  cat  pages  are  saved  when
       man.conf contains the line NOCACHE.

       It is possible to make mmaann suid to a user man. Then, if a cat directory
       has owner man and mode 0755 (only writable by man), and the  cat  files
       have  owner  man  and  mode  0644 or 0444 (only writable by man, or not
       writable at all), no ordinary user can change  the  cat  pages  or  put
       other  files  in the cat directory. If mmaann is not made suid, then a cat
       directory should have mode 0777 if all users should be  able  to  leave
       cat pages there.

       The  option  --cc  forces  reformatting a page, even if a recent cat page
       exists.


HHTTMMLL PPAAGGEESS
       Man will find HTML pages if they live in directories named as  expected
       to  be  ".html", thus a valid name for an HTML version of the llss(1) man
       page would be _/_u_s_r_/_s_h_a_r_e_/_m_a_n_/_h_t_m_l_m_a_n_1_/_l_s_._1_._h_t_m_l.


SSEEAARRCCHH PPAATTHH FFOORR MMAANNUUAALL PPAAGGEESS
       mmaann uses a sophisticated method of finding manual page files, based  on
       the   invocation   options   and   environment   variables,  the  //pprrii--
       vvaattee//eettcc//mmaann..ccoonnff configuration file, and some built in conventions and
       heuristics.

       First  of  all, when the _n_a_m_e argument to mmaann contains a slash (//), mmaann
       assumes it is a file specification itself, and there  is  no  searching
       involved.

       But in the normal case where _n_a_m_e doesn't contain a slash, mmaann searches
       a variety of directories for a file that could be a manual page for the
       topic named.

       If  you  specify  the --MM _p_a_t_h_l_i_s_t option, _p_a_t_h_l_i_s_t is a colon-separated
       list of the directories that mmaann searches.

       If you don't specify --MM but set the MMAANNPPAATTHH environment  variable,  the
       value  of  that  variable  is  the  list  of  the  directories that mmaann
       searches.

       If you don't specify an explicit path list  with  --MM  or  MMAANNPPAATTHH,  mmaann
       develops  its  own path list based on the contents of the configuration
       file //pprriivvaattee//eettcc//mmaann..ccoonnff.  The MMAANNPPAATTHH statements in  the  configura-
       tion  file  identify  particular  directories  to include in the search
       path.

       Furthermore, the MMAANNPPAATTHH__MMAAPP statements add to the search path  depend-
       ing  on your command search path (i.e. your PPAATTHH environment variable).
       For each directory that may be in  the  command  search  path,  a  MMAANN--
       PPAATTHH__MMAAPP  statement  specifies  a directory that should be added to the
       search path for manual page files.  mmaann looks at the PPAATTHH variable  and
       adds the corresponding directories to the manual page file search path.
       Thus, with the proper use of MMAANNPPAATTHH__MMAAPP, when you  issue  the  command
       mmaann  xxyyzz,  you  get a manual page for the program that would run if you
       issued the command xxyyzz.

       In addition, for each directory in the command search path (we'll  call
       it  a  "command  directory")  for  which  you do _n_o_t have a MMAANNPPAATTHH__MMAAPP
       statement, mmaann automatically looks for a manual page directory "nearby"
       namely as a subdirectory in the command directory itself or in the par-
       ent directory of the command directory.

       You can disable the automatic "nearby" searches by  including  a  NNOOAAUU--
       TTOOPPAATTHH statement in //pprriivvaattee//eettcc//mmaann..ccoonnff.

       In  each  directory in the search path as described above, mmaann searches
       for a file named _t_o_p_i_c.._s_e_c_t_i_o_n, with an optional suffix on the  section
       number  and  possibly  a compression suffix.  If it doesn't find such a
       file, it then looks in any subdirectories named mmaann_N or ccaatt_N where _N is
       the  manual section number.  If the file is in a ccaatt_N subdirectory, mmaann
       assumes it is a formatted manual page file (cat page).  Otherwise,  mmaann
       assumes it is unformatted.  In either case, if the filename has a known
       compression suffix (like ..ggzz), mmaann assumes it is gzipped.

       If you want to see where (or if) mmaann would find the manual page  for  a
       particular topic, use the ----ppaatthh (--ww) option.


EENNVVIIRROONNMMEENNTT
       MMAANNPPAATTHH
              If  MMAANNPPAATTHH is set, mmaann uses it as the path to search for manual
              page files.  It overrides the configuration file and  the  auto-
              matic  search  path,  but  is  overridden  by  the --MM invocation
              option.  See SSEEAARRCCHH PPAATTHH FFOORR MMAANNUUAALL PPAAGGEESS.

       MMAANNPPLL  If MMAANNPPLL is set, its value is used as the display  page  length.
              Otherwise, the entire man page will occupy one (long) page.

       MMAANNRROOFFFFSSEEQQ
              If  MMAANNRROOFFFFSSEEQQ is set, its value is used to determine the set of
              preprocessors run before running nnrrooffff or  ttrrooffff.   By  default,
              pages are passed through the tbl preprocessor before nnrrooffff.

       MMAANNSSEECCTT
              If  MMAANNSSEECCTT  is set, its value is used to determine which manual
              sections to search.

       MMAANNWWIIDDTTHH
              If MMAANNWWIIDDTTHH is set, its value is  used  as  the  width  manpages
              should  be displayed.  Otherwise the pages may be displayed over
              the whole width of your screen.

       MMAANNPPAAGGEERR
              If MMAANNPPAAGGEERR is set, its value is used as the name of the program
              to  use to display the man page.  If not, then PPAAGGEERR is used. If
              that has no value either, //uussrr//bbiinn//lleessss --iiss is used.

       BBRROOWWSSEERR
              The name of a browser to use for displaying HTML  manual  pages.
              If it is not set, /usr/bin/less -is is used.

       HHTTMMLLPPAAGGEERR
              The  command to use for rendering HTML manual pages as text.  If
              it is not set, /bin/cat is used.

       LLAANNGG   If LLAANNGG is set, its value defines the name of  the  subdirectory
              where  man first looks for man pages. Thus, the command `LANG=dk
              man 1 foo' will cause man to  look  for  the  foo  man  page  in
              .../dk/man1/foo.1,  and  if  it cannot find such a file, then in
              .../man1/foo.1, where ... is a directory on the search path.

       NNLLSSPPAATTHH,, LLCC__MMEESSSSAAGGEESS,, LLAANNGG
              The environment variables NNLLSSPPAATTHH and LLCC__MMEESSSSAAGGEESS (or LLAANNGG  when
              the  latter  does not exist) play a role in locating the message
              catalog.  (But the English messages are  compiled  in,  and  for
              English no catalog is required.)  Note that programs like ccooll((11))
              called by man also use e.g. LC_CTYPE.

       PPAATTHH   PPAATTHH helps determine the search path for manual page files.  See
              SSEEAARRCCHH PPAATTHH FFOORR MMAANNUUAALL PPAAGGEESS.

       SSYYSSTTEEMM SSYYSSTTEEMM is used to get the default alternate system name (for use
              with the --mm option).

BBUUGGSS
       The --tt option only works if a troff-like program is installed.
       If you see blinking  \255  or  <AD>  instead  of  hyphens,  put  `LESS-
       CHARSET=latin1' in your environment.

TTIIPPSS
       If you add the line

        (global-set-key  [(f1)]  (lambda  () (interactive) (manual-entry (cur-
       rent-word))))

       to your _._e_m_a_c_s file, then hitting F1 will give you the man page for the
       library call at the current cursor position.

       To  get  a  plain  text  version  of a man page, without backspaces and
       underscores, try

         # man foo | col -b > foo.mantxt

AAUUTTHHOORR
       John W. Eaton was the  original  author  of  mmaann.   Zeyd  M.  Ben-Halim
       released  man  1.2,  and  Andries Brouwer followed up with versions 1.3
       thru 1.5p.  Federico  Lucifredi  <flucifredi@acm.org>  is  the  current
       maintainer.

SSEEEE AALLSSOO
       apropos(1), whatis(1), less(1), groff(1), man.conf(5).



                              September 19, 2005                        man(1)
