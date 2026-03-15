#!/usr/bin/env perl

use strict;
use warnings;
use Cwd qw(abs_path);
use File::Spec;

my $theme_dir = shift // "Hate of Nature GTK Theme";
$theme_dir = abs_path($theme_dir)
  or die "error: unable to resolve theme path: $theme_dir\n";

die "error: theme directory not found: $theme_dir\n" unless -d $theme_dir;

my @targets = grep { -f $_ } (
  File::Spec->catfile($theme_dir, "gtk-3.0", "gtk.css"),
  File::Spec->catfile($theme_dir, "gtk-3.0", "gtk-dark.css"),
  File::Spec->catfile($theme_dir, "gtk-4.0", "gtk.css"),
  File::Spec->catfile($theme_dir, "gtk-4.0", "gtk-dark.css"),
);

die "error: no gtk css targets found under $theme_dir\n" unless @targets;

my @required = (
  {
    name    => "Thunar path bar",
    pattern => qr/window\.thunar\s+toolbar#location-toolbar/mi,
  },
  {
    name    => "Thunar sidebar",
    pattern => qr/thunar\s+scrolledwindow\.sidebar/mi,
  },
  {
    name    => "Thunar statusbar",
    pattern => qr/window\.thunar\s+statusbar/mi,
  },
  {
    name    => "Info and help bars",
    pattern => qr/\binfobar\b|banner\s+revealer\s+widget/mi,
  },
  {
    name    => "Notifications and OSD",
    pattern => qr/#XfceNotifyWindow|\.app-notification|\.osd/mi,
  },
  {
    name    => "Popovers and menus",
    pattern => qr/\bpopover\b|menu\s+menuitem|\.context-menu/mi,
  },
  {
    name    => "Tooltips",
    pattern => qr/\btooltip\b/mi,
  },
  {
    name    => "File chooser body",
    pattern => qr/\bfilechooser\b/mi,
  },
  {
    name    => "File chooser sidebar",
    pattern => qr/filechooser\s+placessidebar|#NautilusFileChooser\s+\.sidebar-pane/mi,
  },
  {
    name    => "Portal chooser shell",
    pattern => qr/xdg-desktop-portal-gtk|dialog\.filechooser|window\.filechooser\.csd/mi,
  },
);

my @missing;
for my $file (@targets) {
  open my $fh, "<", $file or die "error: unable to read $file: $!\n";
  local $/;
  my $content = <$fh>;
  close $fh;

  for my $item (@required) {
    next if $content =~ $item->{pattern};
    push @missing, {
      file => $file,
      name => $item->{name},
    };
  }
}

if (!@missing) {
  print "PASS: selector coverage is present in all GTK CSS targets under $theme_dir\n";
  exit 0;
}

print "FAIL: missing required selector coverage in generated theme\n";
for my $entry (@missing) {
  print "  $entry->{file} -> $entry->{name}\n";
}
exit 1;
