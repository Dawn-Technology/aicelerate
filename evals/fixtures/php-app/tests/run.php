<?php

// Minimal test runner: php tests/run.php — exits non-zero on first failure.

spl_autoload_register(function (string $class): void {
    $path = __DIR__ . '/../src/' . str_replace('\\', '/', substr($class, 4)) . '.php';
    if (str_starts_with($class, 'App\\') && file_exists($path)) {
        require $path;
    }
});

function check(bool $cond, string $name): void
{
    if ($cond) {
        echo "PASS: $name\n";
    } else {
        echo "FAIL: $name\n";
        exit(1);
    }
}

$order = new App\Orders\Order(7, 'acme', 12.5, new DateTimeImmutable('2026-03-09'));
$csv = (new App\Export\CsvExporter())->export([$order]);
check(str_contains($csv, "id,customer,total,ordered_at"), 'export has header');
check(str_contains($csv, '7,acme,12.50'), 'export has order row');
check(str_contains($csv, '03/09/2026'), 'export date format');

$editor = new App\Auth\User(1, 'eve', App\Auth\User::ROLE_EDITOR);
check($editor->canEdit(), 'editor can edit');
check(!$editor->canAdministrate(), 'editor cannot administrate');

echo "all tests passed\n";
