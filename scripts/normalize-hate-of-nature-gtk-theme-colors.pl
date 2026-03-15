#!/usr/bin/env perl

use strict;
use warnings;
use Cwd qw(abs_path);
use File::Find;
use File::Spec;

my $include_assets = 0;
my $theme_dir;
my @args = @ARGV;

while (@args) {
  my $arg = shift @args;
  if ($arg eq "--include-assets") {
    $include_assets = 1;
    next;
  }
  if (!defined $theme_dir) {
    $theme_dir = $arg;
    next;
  }
  die "usage: $0 [--include-assets] [theme_dir]\n";
}

$theme_dir //= "Hate of Nature GTK Theme";
$theme_dir = abs_path($theme_dir)
  or die "error: unable to resolve theme path: $theme_dir\n";

die "error: theme directory not found: $theme_dir\n" unless -d $theme_dir;

my @scan_subdirs = qw(gtk-2.0 gtk-3.0 gtk-4.0);
push @scan_subdirs, "assets" if $include_assets;
my @scan_dirs = grep { -d $_ } map { File::Spec->catdir($theme_dir, $_) } @scan_subdirs;
die "error: no GTK theme directories found under $theme_dir\n" unless @scan_dirs;

my @palette_hex = qw(
  000000
  0D1303
  131F00
  162400
  172304
  1A2D00
  223401
  2E4012
  3A5412
  485731
  4A6B1A
  57702F
  5A8A22
  61704A
  86B42B
  92B161
  A6E22E
  E4F0D4
  F8F8F2
);

my @palette_rgb = map { hex_to_rgb($_) } @palette_hex;
my %palette_lookup = map { $_ => 1 } @palette_hex;

my %named_to_rgb = (
  black      => [0, 0, 0],
  white      => [255, 255, 255],
  whitesmoke => [245, 245, 245],
  gray       => [128, 128, 128],
  grey       => [128, 128, 128],
  silver     => [192, 192, 192],
  red        => [255, 0, 0],
  green      => [0, 128, 0],
  blue       => [0, 0, 255],
  yellow     => [255, 255, 0],
  orange     => [255, 165, 0],
  purple     => [128, 0, 128],
  pink       => [255, 192, 203],
  brown      => [165, 42, 42],
);

my @files;
find(
  {
    no_chdir => 1,
    wanted   => sub {
      return unless -f $_;
      my $path = $File::Find::name;
      return
        unless $path =~ m{\.(?:css|scss|svg|rc|xml|theme|ini)$}i
        || $_ eq "gtkrc";
      push @files, $path;
    },
  },
  @scan_dirs
);

my $total_replacements = 0;
my $files_changed = 0;

for my $file (sort @files) {
  open my $fh, "<", $file or die "error: unable to read $file: $!\n";
  local $/;
  my $content = <$fh>;
  close $fh;

  my $original = $content;

  # #rgb, #rgba, #rrggbb, #rrggbbaa
  $content =~ s/#([0-9A-Fa-f]{3,4}|[0-9A-Fa-f]{6}(?:[0-9A-Fa-f]{2})?)\b/replace_hex_token($1, \$total_replacements, \%palette_lookup, \@palette_rgb)/ge;

  # rgb()/rgba()
  $content =~ s/\brgba?\(\s*([0-9]{1,3})\s*[, ]\s*([0-9]{1,3})\s*[, ]\s*([0-9]{1,3})(\s*[,\/]\s*([0-9.]+%?)\s*)?\)/replace_rgba_function($1, $2, $3, $4, \$total_replacements, \@palette_rgb)/ge;

  # GTK CSS old-style: rgba 0, 0, 0, 0.5
  $content =~ s/\b(rgba?|RGBA?|RGBA?)\s+([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})(\s*,\s*([0-9.]+%?))?/replace_legacy_rgba($1, $2, $3, $4, $5, \$total_replacements, \@palette_rgb)/ge;

  # Named colors in value-like positions.
  $content =~ s/(:|\s|,|\()\s*(white|whitesmoke|gray|grey|silver|red|green|blue|yellow|orange|purple|pink|brown)\s*(?=[;,\)])/replace_named_color($1, $2, \$total_replacements, \%named_to_rgb, \@palette_rgb)/gei;

  next if $content eq $original;

  open my $out, ">", $file or die "error: unable to write $file: $!\n";
  print {$out} $content;
  close $out;
  $files_changed++;
}

print "Normalized $total_replacements color tokens across $files_changed files in $theme_dir\n";

exit 0;

sub replace_hex_token {
  my ($raw_hex, $counter_ref, $palette_lookup_ref, $palette_rgb_ref) = @_;
  my ($rgb_hex, $alpha_hex) = split_hex_rgb_alpha($raw_hex);
  return "#$raw_hex" unless defined $rgb_hex;
  return "#" . uc($raw_hex) if $palette_lookup_ref->{uc($rgb_hex)} && !defined $alpha_hex;

  my $rgb_struct = hex_to_rgb($rgb_hex);
  my ($r, $g, $b) = @{$rgb_struct}{qw(r g b)};
  my $nearest = nearest_palette_hex($r, $g, $b, $palette_rgb_ref);
  $$counter_ref++;
  return "#" . $nearest . (defined $alpha_hex ? uc($alpha_hex) : "");
}

sub replace_rgba_function {
  my ($r, $g, $b, $alpha_chunk, $counter_ref, $palette_rgb_ref) = @_;
  return "rgb($r, $g, $b)" unless valid_rgb_triplet($r, $g, $b);

  my $nearest = nearest_palette_hex($r, $g, $b, $palette_rgb_ref);
  my $nearest_rgb = hex_to_rgb($nearest);
  my ($nr, $ng, $nb) = @{$nearest_rgb}{qw(r g b)};
  $$counter_ref++;

  if (defined $alpha_chunk && $alpha_chunk ne "") {
    $alpha_chunk =~ s/^\s*[,\/]\s*//;
    $alpha_chunk =~ s/\s+$//;
    return "rgba($nr, $ng, $nb, $alpha_chunk)";
  }

  return "rgb($nr, $ng, $nb)";
}

sub replace_legacy_rgba {
  my ($fn, $r, $g, $b, $alpha_chunk, $counter_ref, $palette_rgb_ref) = @_;
  return "$fn $r, $g, $b" . (defined $alpha_chunk ? $alpha_chunk : "")
    unless valid_rgb_triplet($r, $g, $b);

  my $nearest = nearest_palette_hex($r, $g, $b, $palette_rgb_ref);
  my $nearest_rgb = hex_to_rgb($nearest);
  my ($nr, $ng, $nb) = @{$nearest_rgb}{qw(r g b)};
  $$counter_ref++;
  return "$fn $nr, $ng, $nb" . (defined $alpha_chunk ? $alpha_chunk : "");
}

sub replace_named_color {
  my ($prefix, $name, $counter_ref, $named_to_rgb_ref, $palette_rgb_ref) = @_;
  my $normalized = lc($name);
  my $rgb = $named_to_rgb_ref->{$normalized};
  return $prefix . $name unless defined $rgb;

  my $nearest = nearest_palette_hex($rgb->[0], $rgb->[1], $rgb->[2], $palette_rgb_ref);
  $$counter_ref++;
  return $prefix . "#" . $nearest;
}

sub split_hex_rgb_alpha {
  my ($raw_hex) = @_;
  my $hex = uc($raw_hex);
  my $len = length($hex);

  if ($len == 3) {
    my @c = split //, $hex;
    return (join("", map { $_ . $_ } @c), undef);
  }
  if ($len == 4) {
    my @c = split //, $hex;
    return (join("", map { $_ . $_ } @c[0 .. 2]), $c[3] . $c[3]);
  }
  if ($len == 6) {
    return ($hex, undef);
  }
  if ($len == 8) {
    return (substr($hex, 0, 6), substr($hex, 6, 2));
  }

  return;
}

sub nearest_palette_hex {
  my ($r, $g, $b, $palette_rgb_ref) = @_;
  my $best_hex = $palette_rgb_ref->[0]->{hex};
  my $best_dist = 10**12;

  for my $entry (@{$palette_rgb_ref}) {
    my $dr = $r - $entry->{r};
    my $dg = $g - $entry->{g};
    my $db = $b - $entry->{b};
    my $dist = $dr * $dr + $dg * $dg + $db * $db;
    if ($dist < $best_dist) {
      $best_dist = $dist;
      $best_hex = $entry->{hex};
    }
  }

  return $best_hex;
}

sub hex_to_rgb {
  my ($hex) = @_;
  $hex = uc($hex);
  return {
    hex => $hex,
    r   => hex(substr($hex, 0, 2)),
    g   => hex(substr($hex, 2, 2)),
    b   => hex(substr($hex, 4, 2)),
  };
}

sub valid_rgb_triplet {
  my ($r, $g, $b) = @_;
  return 0 if $r < 0 || $r > 255;
  return 0 if $g < 0 || $g > 255;
  return 0 if $b < 0 || $b > 255;
  return 1;
}
