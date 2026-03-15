#!/usr/bin/env perl

use strict;
use warnings;
use Cwd qw(abs_path getcwd);
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

die "error: no gtk-3.0/gtk-4.0 css files found under $theme_dir\n" unless @targets;

my $cwd = getcwd();
my @issues;

for my $file (@targets) {
  open my $fh, "<", $file or die "error: unable to read $file: $!\n";
  local $/;
  my $content = <$fh>;
  close $fh;

  my @lines = split /\n/, $content, -1;
  for (my $i = 0; $i < @lines; $i++) {
    my $line = $lines[$i];
    my $line_number = $i + 1;
    my ($value) = $line =~ /^\s*background(?:-color|-image)?\s*:\s*(.*?)\s*;\s*$/i;
    next unless defined $value;
    next unless is_light_background($value);
    push @issues, {
      file => rel_path($file, $cwd),
      line => $line_number,
      value => $value,
    };
  }
}

if (!@issues) {
  print "PASS: no bright background declarations found in $theme_dir\n";
  exit 0;
}

print "FAIL: found " . scalar(@issues) . " bright background declarations in $theme_dir\n";
my $max = 80;
for my $i (0 .. $#issues) {
  last if $i >= $max;
  my $it = $issues[$i];
  print "  $it->{file}:$it->{line} -> background: $it->{value};\n";
}
if (@issues > $max) {
  print "  ... plus " . (@issues - $max) . " more.\n";
}
exit 1;

sub is_light_background {
  my ($value) = @_;
  my $v = lc($value);

  return 1 if $v =~ /#(?:fff|ffffff|fefefe|f8f8f2|e4f0d4)\b/;
  return 1 if $v =~ /\b(?:white|whitesmoke)\b/;

  # Treat opaque near-white rgb() as regressions.
  while ($v =~ /rgb\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*\)/g) {
    return 1 if $1 >= 230 && $2 >= 230 && $3 >= 230;
  }

  # For rgba(), ignore very low alpha glints used for subtle shadows.
  while ($v =~ /rgba\(\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9.]+)\s*\)/g) {
    my ($r, $g, $b, $a) = ($1, $2, $3, $4);
    return 1 if $r == 228 && $g == 240 && $b == 212 && $a >= 0.35;
    next unless $r >= 230 && $g >= 230 && $b >= 230;
    return 1 if $a >= 0.35;
  }

  return 0;
}

sub rel_path {
  my ($path, $base) = @_;
  my $abs = abs_path($path);
  return File::Spec->abs2rel($abs, $base) if defined $abs;
  return $path;
}
