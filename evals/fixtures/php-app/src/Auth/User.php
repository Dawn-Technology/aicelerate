<?php

namespace App\Auth;

class User
{
    public const ROLE_ADMIN = 'admin';
    public const ROLE_EDITOR = 'editor';
    public const ROLE_READER = 'reader';

    public function __construct(
        public readonly int $id,
        public readonly string $name,
        public string $role,
    ) {
    }

    public function canEdit(): bool
    {
        return in_array($this->role, [self::ROLE_ADMIN, self::ROLE_EDITOR], true);
    }

    public function canAdministrate(): bool
    {
        return $this->role === self::ROLE_ADMIN;
    }
}
