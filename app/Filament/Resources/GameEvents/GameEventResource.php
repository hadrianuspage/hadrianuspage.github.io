<?php

namespace App\Filament\Resources\GameEvents;

use App\Filament\Resources\GameEvents\Pages;
use App\Filament\Resources\GameEvents\RelationManagers;
use App\Models\GameEvent;
use BackedEnum;
use Filament\Forms;
use Filament\Schemas\Schema;
use Filament\Resources\Resource;
use Filament\Support\Icons\Heroicon;
use Filament\Tables;
use Filament\Tables\Table;
use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\SoftDeletingScope;

class GameEventResource extends Resource
{
    protected static ?string $model = GameEvent::class;

    protected static string|BackedEnum|null $navigationIcon = Heroicon::OutlinedCalendar;

    public static function form(Schema $schema): Schema
    {
        return $schema
            ->components([
                Forms\Components\TextInput::make('title')
                    ->required()
                    ->maxLength(255),
                Forms\Components\Select::make('type')
                    ->options([
                        'seasonal' => 'Seasonal Event',
                        'package' => 'Package/Deal',
                    ])
                    ->required(),
                Forms\Components\TextInput::make('image_url')
                    ->label('Image URL')
                    ->required()
                    ->maxLength(255)
                    ->helperText('Full URL to the image (SWF/JPG/PNG).'),
                Forms\Components\Textarea::make('description')
                    ->maxLength(65535)
                    ->columnSpanFull(),
                Forms\Components\Toggle::make('active')
                    ->required()
                    ->default(true),
                Forms\Components\KeyValue::make('data')
                    ->label('Extra Data')
                    ->keyLabel('Key')
                    ->valueLabel('Value')
                    ->columnSpanFull(),
            ]);
    }

    public static function table(Table $table): Table
    {
        return $table
            ->columns([
                Tables\Columns\TextColumn::make('title')
                    ->searchable(),
                Tables\Columns\TextColumn::make('type')
                    ->badge()
                    ->color(fn (string $state): string => match ($state) {
                        'seasonal' => 'success',
                        'package' => 'warning',
                        default => 'gray',
                    }),
                Tables\Columns\ImageColumn::make('image_url')
                    ->label('Preview')
                    ->checkFileExistence(false), // External URLs
                Tables\Columns\IconColumn::make('active')
                    ->boolean(),
                Tables\Columns\TextColumn::make('created_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                Tables\Columns\TextColumn::make('updated_at')
                    ->dateTime()
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->filters([
                //
            ])
            ->actions([
                \Filament\Actions\EditAction::make(),
            ])
            ->bulkActions([
                \Filament\Actions\BulkActionGroup::make([
                    \Filament\Actions\DeleteBulkAction::make(),
                ]),
            ]);
    }

    public static function getRelations(): array
    {
        return [
            //
        ];
    }

    public static function getPages(): array
    {
        return [
            'index' => Pages\ListGameEvents::route('/'),
            'create' => Pages\CreateGameEvent::route('/create'),
            'edit' => Pages\EditGameEvent::route('/{record}/edit'),
        ];
    }
}