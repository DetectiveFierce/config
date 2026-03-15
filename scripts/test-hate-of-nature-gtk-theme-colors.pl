#!/usr/bin/env perl

use strict;
use warnings;
use Cwd qw(abs_path getcwd);
use File::Find;
use File::Spec;

my $include_assets = 0;
my $max_colors_to_print = 60;
my $theme_dir;
my @args = @ARGV;

while (@args) {
  my $arg = shift @args;
  if ($arg eq "--include-assets") {
    $include_assets = 1;
    next;
  }
  if ($arg eq "--max-colors") {
    my $value = shift @args;
    die "usage: $0 [--include-assets] [--max-colors N] [theme_dir]\n"
      unless defined $value && $value =~ /^\d+$/;
    $max_colors_to_print = int($value);
    next;
  }
  if ($arg =~ /^--max-colors=(\d+)$/) {
    $max_colors_to_print = int($1);
    next;
  }
  if (!defined $theme_dir) {
    $theme_dir = $arg;
    next;
  }
  die "usage: $0 [--include-assets] [--max-colors N] [theme_dir]\n";
}

$theme_dir //= "Hate of Nature GTK Theme";
$theme_dir = abs_path($theme_dir)
  or die "error: unable to resolve theme path: $theme_dir\n";

die "error: theme directory not found: $theme_dir\n" unless -d $theme_dir;

my @scan_subdirs = qw(gtk-2.0 gtk-3.0 gtk-4.0);
push @scan_subdirs, "assets" if $include_assets;
my @scan_dirs = grep { -d $_ } map { File::Spec->catdir($theme_dir, $_) } @scan_subdirs;
die "error: no GTK theme directories found under $theme_dir\n" unless @scan_dirs;

my %allowed_rgb = map { $_ => 1 } qw(
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

my %allowed_named = map { $_ => 1 } qw(black transparent);
my @named_candidates = qw(
  white
  whitesmoke
  gray
  grey
  silver
  red
  green
  blue
  orange
  yellow
  purple
  pink
  brown
  black
);
my $named_regex = join "|", @named_candidates;

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

my $cwd = getcwd();
my %offenders;
my $total_issues = 0;
my $max_examples_per_color = 5;

for my $file (sort @files) {
  open my $fh, "<", $file or die "error: unable to read $file: $!\n";
  local $/;
  my $content = <$fh>;
  close $fh;

  # Drop comment blocks before scanning to reduce false positives.
  $content =~ s{/\*.*?\*/}{}gs;
  $content =~ s{<!--.*?-->}{}gs;
  $content =~ s{^\s*//.*$}{}mg;
  $content =~ s{^\s*[;!].*$}{}mg;
  $content =~ s{^\s*#(?![0-9A-Fa-f]{3,8}\b).*$}{}mg;

  my @lines = split /\n/, $content, -1;
  for (my $i = 0; $i < @lines; $i++) {
    my $line = $lines[$i];
    my $line_number = $i + 1;

    while ($line =~ /#[0-9A-Fa-f]{3,8}\b/g) {
      my $raw = $&;
      my $rgb = normalize_hex_rgb($raw);
      next unless defined $rgb;
      next if $allowed_rgb{$rgb};
      record_issue(
        \%offenders,
        $max_examples_per_color,
        "#$rgb",
        to_relative_path($file, $cwd),
        $line_number,
        $raw
      );
      $total_issues++;
    }

    while ($line =~ /\brgba?\(\s*([0-9]{1,3})\s*[, ]\s*([0-9]{1,3})\s*[, ]\s*([0-9]{1,3})(?:\s*[,\/]\s*([0-9.]+%?))?\s*\)/gi) {
      my ($r, $g, $b) = ($1, $2, $3);
      next unless valid_rgb_triplet($r, $g, $b);
      my $rgb = sprintf("%02X%02X%02X", $r, $g, $b);
      next if $allowed_rgb{$rgb};
      my $raw = $&;
      record_issue(
        \%offenders,
        $max_examples_per_color,
        "#$rgb",
        to_relative_path($file, $cwd),
        $line_number,
        $raw
      );
      $total_issues++;
    }

    # GTK CSS sometimes writes "rgba 0, 0, 0, 0.5" without parentheses.
    while ($line =~ /\brgba?\s+([0-9]{1,3})\s*,\s*([0-9]{1,3})\s*,\s*([0-9]{1,3})(?:\s*,\s*([0-9.]+%?))?/gi) {
      my ($r, $g, $b) = ($1, $2, $3);
      next unless valid_rgb_triplet($r, $g, $b);
      my $rgb = sprintf("%02X%02X%02X", $r, $g, $b);
      next if $allowed_rgb{$rgb};
      my $raw = $&;
      record_issue(
        \%offenders,
        $max_examples_per_color,
        "#$rgb",
        to_relative_path($file, $cwd),
        $line_number,
        $raw
      );
      $total_issues++;
    }

    while ($line =~ /(?:[:\s,(])\s*($named_regex)\s*(?=[;,)])/gi) {
      my $raw = $1;
      my $normalized = lc $raw;
      next if $allowed_named{$normalized};
      record_issue(
        \%offenders,
        $max_examples_per_color,
        $normalized,
        to_relative_path($file, $cwd),
        $line_number,
        $raw
      );
      $total_issues++;
    }
  }
}

if ($total_issues == 0) {
  print "PASS: no out-of-palette colors found in $theme_dir\n";
  exit 0;
}

print "FAIL: found $total_issues out-of-palette color references in $theme_dir\n";
my @sorted_colors = sort {
  $offenders{$b}->{count} <=> $offenders{$a}->{count}
    || $a cmp $b
} keys %offenders;

my $printed = 0;
for my $color (@sorted_colors) {
  last if $max_colors_to_print > 0 && $printed >= $max_colors_to_print;
  my $entry = $offenders{$color};
  print "\n$color ($entry->{count} occurrences)\n";
  for my $example (@{$entry->{examples}}) {
    print "  $example->{file}:$example->{line} -> $example->{raw}\n";
  }
  $printed++;
}

if ($max_colors_to_print > 0 && @sorted_colors > $max_colors_to_print) {
  my $remaining = @sorted_colors - $max_colors_to_print;
  print "\n... plus $remaining more color groups not shown.\n";
  print "Re-run with --max-colors 0 to show all groups.\n";
}

exit 1;

sub normalize_hex_rgb {
  my ($token) = @_;
  my $hex = uc $token;
  $hex =~ s/^#//;

  if (length($hex) == 3 || length($hex) == 4) {
    my @chars = split //, $hex;
    return uc(join("", map { $_ . $_ } @chars[0 .. 2]));
  }

  if (length($hex) == 6 || length($hex) == 8) {
    return substr($hex, 0, 6);
  }

  return;
}

sub valid_rgb_triplet {
  my ($r, $g, $b) = @_;
  return 0 if $r < 0 || $r > 255;
  return 0 if $g < 0 || $g > 255;
  return 0 if $b < 0 || $b > 255;
  return 1;
}

sub record_issue {
  my ($store, $max_examples, $color, $file, $line, $raw) = @_;
  $store->{$color}->{count}++;
  if (!exists $store->{$color}->{examples} || @{$store->{$color}->{examples}} < $max_examples) {
    push @{$store->{$color}->{examples}}, {
      file => $file,
      line => $line,
      raw  => $raw,
    };
  }
}

sub to_relative_path {
  my ($path, $base) = @_;
  my $abs_pathname = abs_path($path);
  return File::Spec->abs2rel($abs_pathname, $base) if defined $abs_pathname;
  return $path;
}
