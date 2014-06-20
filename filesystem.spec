Summary: The basic directory layout for a Linux system
Name: filesystem
Version: 3.2
Release: 1
License: Public Domain
URL: https://fedorahosted.org/filesystem
Group: System/Base
BuildArch: noarch
Buildroot: %{_tmppath}/%{name}-%{version}-%{release}-root
# Raw source1 URL: https://fedorahosted.org/filesystem/browser/lang-exceptions?format=raw
Source1: https://fedorahosted.org/filesystem/browser/lang-exceptions
Source2: iso_639.sed
Source3: iso_3166.sed
Requires(pre): setup >= 2.5.4-1
BuildRequires: iso-codes
# The /run got moved in systemd 187 to this package, thus conflicts with older ones.
Conflicts: systemd < 187

%description
The filesystem package is one of the basic packages that is installed
on a Linux system. Filesystem contains the basic directory layout
for a Linux operating system, including the correct permissions for
the directories.

%prep
rm -f $RPM_BUILD_DIR/filelist

%build

%install
rm -rf %{buildroot}
mkdir %{buildroot}
install -p -c -m755 %SOURCE2 %{buildroot}/iso_639.sed
install -p -c -m755 %SOURCE3 %{buildroot}/iso_3166.sed

cd %{buildroot}

mkdir -p boot dev \
        etc/{X11/{applnk,fontpath.d},xdg/autostart,opt,pm/{config.d,power.d,sleep.d},xinetd.d,skel,sysconfig,pki,bash_completion.d} \
        home media mnt opt proc root run srv sys tmp \
        usr/{bin,games,include,%{_lib}/{games,sse2,tls,X11,pm-utils/{module.d,power.d,sleep.d}},lib/{debug/usr,games,locale,modules,sse2},libexec,local/{bin,etc,games,lib,%{_lib},sbin,src,share/{applications,man/man{1,2,3,4,5,6,7,8,9,n,1x,2x,3x,4x,5x,6x,7x,8x,9x},info},libexec,include,},sbin,share/{aclocal,appdata,applications,augeas/lenses,backgrounds,desktop-directories,dict,doc,empty,games,ghostscript/conf.d,gnome,icons,idl,info,man/man{1,2,3,4,5,6,7,8,9,n,1x,2x,3x,4x,5x,6x,7x,8x,9x,0p,1p,3p},mime-info,misc,omf,pixmaps,sounds,themes,xsessions,X11},src,src/kernels,src/debug} \
        var/{adm,empty,gopher,lib/{games,misc,rpm-state},local,log,nis,preserve,spool/{mail,lpd},tmp,db,cache,opt,games,yp}

#do not create the symlink atm.
#ln -snf etc/sysconfig etc/default
ln -snf ../var/tmp usr/tmp
ln -snf spool/mail var/mail
ln -snf usr/bin bin
ln -snf usr/sbin sbin
ln -snf usr/lib lib
ln -snf usr/%{_lib} %{_lib}
ln -snf ../run var/run
ln -snf ../run/lock var/lock
ln -snf usr/bin usr/lib/debug/bin
ln -snf usr/lib usr/lib/debug/lib
ln -snf usr/%{_lib} usr/lib/debug/%{_lib}
ln -snf ../.dwz usr/lib/debug/usr/.dwz
ln -snf usr/sbin usr/lib/debug/sbin

sed -n -f %{buildroot}/iso_639.sed /usr/share/xml/iso-codes/iso_639.xml \
  >%{buildroot}/iso_639.tab
sed -n -f %{buildroot}/iso_3166.sed /usr/share/xml/iso-codes/iso_3166.xml \
  >%{buildroot}/iso_3166.tab

grep -v "^$" %{buildroot}/iso_639.tab | grep -v "^#" | while read a b c d ; do
    [[ "$d" =~ "^Reserved" ]] && continue
    [[ "$d" =~ "^No linguistic" ]] && continue

    locale=$c
    if [ "$locale" = "XX" ]; then
        locale=$b
    fi
    echo "%lang(${locale})	/usr/share/locale/${locale}" >> $RPM_BUILD_DIR/filelist
    echo "%lang(${locale}) %ghost %config(missingok) /usr/share/man/${locale}" >>$RPM_BUILD_DIR/filelist
done
cat %{SOURCE1} | grep -v "^#" | grep -v "^$" | while read loc ; do
    locale=$loc
    locality=
    special=
    [[ "$locale" =~ "@" ]] && locale=${locale%%%%@*}
    [[ "$locale" =~ "_" ]] && locality=${locale##*_}
    [[ "$locality" =~ "." ]] && locality=${locality%%%%.*}
    [[ "$loc" =~ "_" ]] || [[ "$loc" =~ "@" ]] || special=$loc

    # If the locality is not official, skip it
    if [ -n "$locality" ]; then
        grep -q "^$locality" %{buildroot}/iso_3166.tab || continue
    fi
    # If the locale is not official and not special, skip it
    if [ -z "$special" ]; then
        egrep -q "[[:space:]]${locale%%_*}[[:space:]]" \
           %{buildroot}/iso_639.tab || continue
    fi
    echo "%lang(${locale})	/usr/share/locale/${loc}" >> $RPM_BUILD_DIR/filelist
    echo "%lang(${locale})  %ghost %config(missingok) /usr/share/man/${loc}" >> $RPM_BUILD_DIR/filelist
done

rm -f %{buildroot}/iso_639.tab
rm -f %{buildroot}/iso_639.sed
rm -f %{buildroot}/iso_3166.tab
rm -f %{buildroot}/iso_3166.sed

cat $RPM_BUILD_DIR/filelist | grep "locale" | while read a b ; do
    mkdir -p -m 755 %{buildroot}/$b/LC_MESSAGES
done

cat $RPM_BUILD_DIR/filelist | grep "/share/man" | while read a b c d; do
    mkdir -p -m 755 %{buildroot}/$d/man{1,2,3,4,5,6,7,8,9,n,1x,2x,3x,4x,5x,6x,7x,8x,9x,0p,1p,3p}
done

for i in man{1,2,3,4,5,6,7,8,9,n,1x,2x,3x,4x,5x,6x,7x,8x,9x,0p,1p,3p}; do
   echo "/usr/share/man/$i" >>$RPM_BUILD_DIR/filelist
done

%pretrans -p <lua>
--# If we are running in pretrans in a fresh root, there is no /usr and
--# symlinks. We cannot be sure, to be the very first rpm in the
--# transaction list. Let's create the needed base directories and symlinks
--# here, to place the files from other packages in the right locations.
--# When our rpm is unpacked by cpio, it will set all permissions and modes
--# later.
posix.mkdir("/usr")
posix.mkdir("/usr/bin")
posix.mkdir("/usr/sbin")
posix.mkdir("/usr/lib")
posix.mkdir("/usr/lib/debug")
posix.mkdir("/usr/lib/debug/usr/")
posix.mkdir("/usr/%{_lib}")
posix.symlink("usr/bin", "/bin")
posix.symlink("usr/sbin", "/sbin")
posix.symlink("usr/lib", "/lib")
posix.symlink("usr/bin", "/usr/lib/debug/bin")
posix.symlink("usr/lib", "/usr/lib/debug/lib")
posix.symlink("usr/%{_lib}", "/usr/lib/debug/%{_lib}")
posix.symlink("../.dwz", "/usr/lib/debug/usr/.dwz")
posix.symlink("usr/sbin", "/usr/lib/debug/sbin")
posix.symlink("usr/%{_lib}", "/%{_lib}")
posix.mkdir("/run")
posix.symlink("../run", "/var/run")
posix.symlink("../run/lock", "/var/lock")
return 0

%posttrans
#we need to restorecon on some dirs created in %pretrans or by other packages
restorecon /var/run 2>/dev/null >/dev/null || :
restorecon /var/lock 2>/dev/null >/dev/null || :
restorecon -r /usr/lib/debug/ 2>/dev/null >/dev/null || :
restorecon /sys 2>/dev/null >/dev/null || :
restorecon /boot 2>dev/null >/dev/null || :
restorecon /proc 2>dev/null >/dev/null || :
restorecon /dev 2>dev/null >/dev/null || :

%files -f filelist
%exclude /documentation.list
%defattr(0755,root,root,-)
%dir %attr(555,root,root) /
/bin
%attr(555,root,root) /boot
/dev
%dir /etc
/etc/X11
/etc/xdg
/etc/opt
/etc/pm
/etc/xinetd.d
/etc/skel
/etc/sysconfig
/etc/pki
/etc/bash_completion.d/
/home
/lib
%ifarch x86_64 ppc64 sparc64 s390x aarch64 ppc64le
/%{_lib}
%endif
/media
%dir /mnt
%dir /opt
%attr(555,root,root) /proc
%attr(550,root,root) /root
/run
/sbin
/srv
%attr(555,root,root) /sys
%attr(1777,root,root) /tmp
%dir /usr
%attr(555,root,root) /usr/bin
/usr/games
/usr/include
%dir %attr(555,root,root) /usr/lib
%dir /usr/lib/debug
%ghost /usr/lib/debug/bin
%ghost /usr/lib/debug/lib
%ghost /usr/lib/debug/%{_lib}
%ghost /usr/lib/debug/usr
%ghost /usr/lib/debug/usr/.dwz
%ghost /usr/lib/debug/sbin
%attr(555,root,root) /usr/lib/games
%attr(555,root,root) /usr/lib/sse2
%ifarch x86_64 ppc64 sparc64 s390x aarch64 ppc64le
%attr(555,root,root) /usr/%{_lib}
%else
%attr(555,root,root) /usr/lib/tls
%attr(555,root,root) /usr/lib/X11
%attr(555,root,root) /usr/lib/pm-utils
%endif
/usr/libexec
/usr/local
%attr(555,root,root) /usr/sbin
%dir /usr/share
/usr/share/aclocal
/usr/share/appdata
/usr/share/applications
/usr/share/augeas
/usr/share/backgrounds
/usr/share/desktop-directories
/usr/share/dict
/usr/share/doc
%attr(555,root,root) %dir /usr/share/empty
/usr/share/games
/usr/share/ghostscript
/usr/share/gnome
/usr/share/icons
/usr/share/idl
/usr/share/info
%dir /usr/share/locale
%dir /usr/share/man
/usr/share/mime-info
/usr/share/misc
/usr/share/omf
/usr/share/pixmaps
/usr/share/sounds
/usr/share/themes
/usr/share/xsessions
/usr/share/X11
/usr/src
/usr/tmp
%dir /var
/var/adm
/var/cache
/var/db
/var/empty
/var/games
/var/gopher
/var/lib
/var/local
%ghost /var/lock
/var/log
/var/mail
/var/nis
/var/opt
/var/preserve
%ghost /var/run
%dir /var/spool
%attr(755,root,root) /var/spool/lpd
%attr(775,root,mail) /var/spool/mail
%attr(1777,root,root) /var/tmp
/var/yp

